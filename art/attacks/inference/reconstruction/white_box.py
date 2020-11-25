# MIT License
#
# Copyright (C) The Adversarial Robustness Toolbox (ART) Authors 2020
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
This module implements database reconstruction attacks.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
from typing import Optional

import numpy as np
import sklearn
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from scipy.optimize import fmin_l_bfgs_b

from art.attacks import InferenceAttack
from art.estimators.estimator import BaseEstimator
from art.estimators.classification.classifier import ClassifierMixin
from art.estimators.classification.scikitlearn import ScikitlearnEstimator

logger = logging.getLogger(__name__)


class DatabaseReconstruction(InferenceAttack):

    _estimator_requirements = (BaseEstimator, ClassifierMixin, ScikitlearnEstimator)

    def __init__(self, estimator):
        super().__init__(estimator=estimator)

        self.params = self.estimator.get_trainable_attribute_names()

    @staticmethod
    def objective(x, y, x_train, y_train, private_estimator, parent_model, params):
        """Objective function which we seek to minimise"""

        model = sklearn.base.clone(parent_model.model, safe=True)
        model.fit(np.vstack((x_train, x)), np.hstack((y_train, y)))

        residual = 0.0

        for param in params:
            residual += np.sum((model.__getattribute__(param) - private_estimator.model.__getattribute__(param)) ** 2)

        return residual

    def infer(self, x: np.ndarray, y: Optional[np.ndarray] = None, **kwargs) -> np.ndarray:

        tol = float("inf")
        x0 = x[0, :]
        x_guess = None
        y_guess = None

        for _y in np.unique(y):
            args = (_y, x, y, self._estimator, self.estimator, self.params)
            _x, _tol, _ = fmin_l_bfgs_b(
                self.objective, x0, args=args, approx_grad=True, factr=100, pgtol=1e-10, bounds=None
            )

            if _tol < tol:
                tol = _tol
                x_guess = _x
                y_guess = _y

        return x_guess  # , y_guess, tol
