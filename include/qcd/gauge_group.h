#pragma once

#include <Eigen/Dense>
#include <algorithm>
#include <cmath>
#include <complex>
#include <numbers>
#include <qcd/rng.h>

namespace qcd {
    struct U1 {
        using Link = std::complex<double>;
        static Link identity() { return {1., 0.}; }
        static Link zero() { return {}; }
        static Link dagger(Link u) { return std::conj(u); }
        static Link multiply(Link a, Link b) { return a * b; }
        static double trace(Link u) { return u.real(); }

        static Link proposal(rng::RandomStream &r, double scale) {
            return std::polar(1., scale * (2. * r.uniform_unit() - 1.));
        }

        static Link hot(rng::RandomStream &r) { return proposal(r, std::numbers::pi); }
    };

    struct SU3 {
        using Link = Eigen::Matrix3cd;
        static Link identity() { return Link::Identity(); }
        static Link zero() { return Link::Zero(); }
        static Link dagger(const Link &u) { return u.adjoint(); }
        static Link multiply(const Link &a, const Link &b) { return a * b; }
        static double trace(const Link &u) { return u.trace().real() / 3.; }
        // A uniform axis and symmetric angle in a randomly chosen embedded SU(2).
        // Each rotation and its inverse have identical proposal probability.
        static Link proposal(rng::RandomStream &r, double scale) {
            constexpr int pairs[3][2] = {{0, 1}, {0, 2}, {1, 2}};
            const auto p = r.uniform_index(3);
            const int i = pairs[p][0], j = pairs[p][1];
            const double theta = scale * (2. * r.uniform_unit() - 1.);
            const double z = 2. * r.uniform_unit() - 1.;
            const double phi = 2. * std::numbers::pi * r.uniform_unit();
            const double transverse = std::sqrt(1. - z * z);
            const double s = std::sin(theta);
            const std::complex<double> a{std::cos(theta), s * z};
            const std::complex<double> b{
                s * transverse * std::sin(phi),
                s * transverse * std::cos(phi)
            };
            Link u = identity();
            u(i, i) = a;
            u(i, j) = b;
            u(j, i) = -std::conj(b);
            u(j, j) = std::conj(a);
            return u;
        }

        static Link hot(rng::RandomStream &r) {
            // Complex Ginibre QR with diagonal phase correction gives Haar U(3).
            Link z;
            for (int i = 0; i < 3; ++i)
                for (int j = 0; j < 3; ++j) {
                    const double a = std::sqrt(-2. * std::log(std::max(r.uniform_unit(), 1e-300)));
                    const double b = 2. * std::numbers::pi * r.uniform_unit();
                    z(i, j) = std::polar(a, b);
                }
            Eigen::HouseholderQR<Link> qr(z);
            Link q = qr.householderQ();
            for (int i = 0; i < 3; ++i) {
                const std::complex<double> d = qr.matrixQR()(i, i);
                q.col(i) *= d / std::abs(d);
            }
            q.col(0) *= std::conj(q.determinant());
            return q;
        }
    };
} // namespace qcd
