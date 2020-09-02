#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import division

import numpy as np

import neurogym as ngym
from neurogym import spaces


class DelayMatchCategory(ngym.TrialEnv):
    r"""Delay match-to-category task.

    A sample stimulus is followed by a delay and test. Agents are required
    to indicate if the sample and test are in the same category.
    """
    metadata = {
        'paper_link': 'https://www.nature.com/articles/nature05078',
        'paper_name': '''Experience-dependent representation
        of visual categories in parietal cortex''',
        'tags': ['perceptual', 'working memory', 'two-alternative',
                 'supervised']
    }

    def __init__(self, dt=100, rewards=None, timing=None, sigma=1.0,
                 dim_ring=2):
        super().__init__(dt=dt)
        self.choices = ['match', 'non-match']  # match, non-match

        self.sigma = sigma / np.sqrt(self.dt)  # Input noise

        # Rewards
        self.rewards = {'abort': -0.1, 'correct': +1., 'fail': 0.}
        if rewards:
            self.rewards.update(rewards)

        self.timing = {
            'fixation': 500,
            'sample': 650,
            'first_delay': 1000,
            'test': 650}

        if timing:
            self.timing.update(timing)

        self.abort = False

        self.theta = np.linspace(0, 2 * np.pi, dim_ring + 1)[:-1]

        name = {'fixation': 0, 'stimulus': range(1, dim_ring + 1)}
        self.observation_space = spaces.Box(
            -np.inf, np.inf, shape=(1 + dim_ring,), dtype=np.float32, name=name)

        name = {'fixation': 0, 'match': 1, 'non-match': 2}
        self.action_space = spaces.Discrete(3, name=name)

    def _new_trial(self, **kwargs):
        # Trial info
        trial = {
            'ground_truth': self.rng.choice(self.choices),
            'sample_category': self.rng.choice([0, 1]),
        }
        trial.update(**kwargs)

        ground_truth = trial['ground_truth']
        sample_category = trial['sample_category']
        if ground_truth == 'match':
            test_category = sample_category
        else:
            test_category = 1 - sample_category

        sample_theta = (sample_category + self.rng.rand()) * np.pi
        test_theta = (test_category + self.rng.rand()) * np.pi

        stim_sample = np.cos(self.theta - sample_theta) * 0.5 + 0.5
        stim_test = np.cos(self.theta - test_theta) * 0.5 + 0.5

        # Periods
        periods = ['fixation', 'sample', 'first_delay', 'test']
        self.add_period(periods)
        # self.add_period('decision', after='test')

        self.add_ob(1, where='fixation')
        self.set_ob(0, 'test', where='fixation')
        self.add_ob(stim_sample, 'sample', where='stimulus')
        self.add_ob(stim_test, 'test', where='stimulus')
        self.add_randn(0, self.sigma, ['sample', 'test'], where='stimulus')

        self.set_groundtruth(self.action_space.name[ground_truth], 'test')

        return trial

    def _step(self, action, **kwargs):
        new_trial = False

        obs = self.ob_now
        gt = self.gt_now

        reward = 0
        if self.in_period('fixation'):
            if action != 0:
                new_trial = self.abort
                reward = self.rewards['abort']
        elif self.in_period('test'):
            if action != 0:
                new_trial = True
                if action == gt:
                    reward = self.rewards['correct']
                    self.performance = 1
                else:
                    reward = self.rewards['fail']

        return obs, reward, False, {'new_trial': new_trial, 'gt': gt}
