#pragma once

#include <qcd/action.h>

namespace qcd {
    template<class G>
    double metropolis(Field<G> &f, rng::RandomStream &r, double beta, double scale) {
        std::size_t accepted = 0;
        for (std::size_t x = 0; x < f.geometry.volume(); ++x)
            for (std::size_t mu = 0; mu < f.geometry.dimension_count(); ++mu) {
                const auto candidate = G::multiply(G::proposal(r, scale), f.at(x, mu));
                const double delta = action_difference(f, x, mu, candidate, beta);
                if (delta <= 0. || r.uniform_unit() < std::exp(-delta)) {
                    f.at(x, mu) = candidate;
                    ++accepted;
                }
            }
        return static_cast<double>(accepted) / static_cast<double>(f.links.size());
    }
} // namespace qcd
