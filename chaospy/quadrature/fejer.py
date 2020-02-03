# -*- coding: utf-8 -*-
"""
Fejér proposed two quadrature rules very similar to :ref:`clenshaw_curtis`.
The only difference is that the endpoints are set to zero. That is, Fejér only
used the interior extrema of the Chebyshev polynomials, i.e. the true
stationary points. This makes this a better method for performing quadrature on
infinite intervals, as the evaluation does not contain illegal values.

Example usage
-------------

The first few orders with linear growth rule::

    >>> distribution = chaospy.Uniform(0, 1)
    >>> for order in [0, 1, 2, 3]:
    ...     abscissas, weights = chaospy.generate_quadrature(
    ...         order, distribution, rule="fejer")
    ...     print(order, abscissas.round(3), weights.round(3))
    0 [[0.5]] [1.]
    1 [[0.25 0.75]] [0.5 0.5]
    2 [[0.146 0.5   0.854]] [0.286 0.429 0.286]
    3 [[0.095 0.345 0.655 0.905]] [0.188 0.312 0.312 0.188]

The first few orders with exponential growth rule::

    >>> for order in [0, 1, 2]:  # doctest: +NORMALIZE_WHITESPACE
    ...     abscissas, weights = chaospy.generate_quadrature(
    ...         order, distribution, rule="fejer", growth=True)
    ...     print(order, abscissas.round(2), weights.round(2))
    0 [[0.5]] [1.]
    1 [[0.15 0.5  0.85]] [0.29 0.43 0.29]
    2 [[0.04 0.15 0.31 0.5  0.69 0.85 0.96]]
        [0.07 0.14 0.18 0.2  0.18 0.14 0.07]

Applying the rule using Smolyak sparse grid::

    >>> distribution = chaospy.Iid(chaospy.Uniform(0, 1), 2)
    >>> abscissas, weights = chaospy.generate_quadrature(
    ...     2, distribution, rule="fejer", growth=True, sparse=True)
    >>> abscissas.round(3)
    array([[0.038, 0.146, 0.146, 0.146, 0.309, 0.5  , 0.5  , 0.5  , 0.5  ,
            0.5  , 0.5  , 0.5  , 0.691, 0.854, 0.854, 0.854, 0.962],
           [0.5  , 0.146, 0.5  , 0.854, 0.5  , 0.038, 0.146, 0.309, 0.5  ,
            0.691, 0.854, 0.962, 0.5  , 0.146, 0.5  , 0.854, 0.5  ]])
    >>> weights.round(3)
    array([ 0.074,  0.082, -0.021,  0.082,  0.184,  0.074, -0.021,  0.184,
           -0.273,  0.184, -0.021,  0.074,  0.184,  0.082, -0.021,  0.082,
            0.074])
"""
from __future__ import division

import numpy

from .combine import combine_quadrature


def quad_fejer(order, domain=(0, 1), growth=False):
    """
    Generate the quadrature abscissas and weights in Fejer quadrature.

    Args:
        order (int, numpy.ndarray):
            Quadrature order.
        domain (chaospy.distributions.baseclass.Dist, numpy.ndarray):
            Either distribution or bounding of interval to integrate over.
        growth (bool):
            If True sets the growth rule for the quadrature rule to only
            include orders that enhances nested samples.

    Returns:
        (numpy.ndarray, numpy.ndarray):
            abscissas:
                The quadrature points for where to evaluate the model function
                with ``abscissas.shape == (len(dist), N)`` where ``N`` is the
                number of samples.
            weights:
                The quadrature weights with ``weights.shape == (N,)``.

    Example:
        >>> abscissas, weights = quad_fejer(3, (0, 1))
        >>> abscissas.round(4)
        array([[0.0955, 0.3455, 0.6545, 0.9045]])
        >>> weights.round(4)
        array([0.1804, 0.2996, 0.2996, 0.1804])
    """
    from ..distributions.baseclass import Dist
    if isinstance(domain, Dist):
        abscissas, weights = quad_fejer(
            order, (domain.lower, domain.upper), growth)
        weights *= domain.pdf(abscissas).flatten()
        weights /= numpy.sum(weights)
        return abscissas, weights

    order = numpy.asarray(order, dtype=int).flatten()
    lower, upper = numpy.array(domain)
    lower = numpy.asarray(lower).flatten()
    upper = numpy.asarray(upper).flatten()

    dim = max(lower.size, upper.size, order.size)

    order = numpy.ones(dim, dtype=int)*order
    lower = numpy.ones(dim)*lower
    upper = numpy.ones(dim)*upper

    if growth:
        order = numpy.where(order > 0, 2**(order+1)-2, 0)

    abscissas, weights = zip(*[_fejer(order_) for order_ in order])

    return combine_quadrature(abscissas, weights, (lower, upper))


def _fejer(order):
    """Backend method."""
    order = int(order)
    if order == 0:
        return numpy.array([.5]), numpy.array([1.])

    order += 2

    theta = (order-numpy.arange(order+1))*numpy.pi/order
    abscisas = 0.5*numpy.cos(theta) + 0.5

    idx, idy = numpy.mgrid[:order+1, :order//2]
    weights = 2*numpy.cos(2*(idy+1)*theta[idx])/(4*idy*(idy+2)+3)
    if order % 2 == 0:
        weights[:, -1] *= 0.5
    weights = (1-numpy.sum(weights, -1)) / order

    return abscisas[1:-1], weights[1:-1]
