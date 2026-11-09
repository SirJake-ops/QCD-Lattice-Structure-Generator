#pragma once

#include <qcd/gauge_field.h>

namespace qcd {
    template<class G>
    typename G::Link plaquette_matrix(const Field<G> &f, std::size_t x, std::size_t mu,
                                      std::size_t nu) {
        const auto &l = f.geometry;
        return G::multiply(G::multiply(G::multiply(f.at(x, mu), f.at(l.forward_neighbor(x, mu), nu)),
                                       G::dagger(f.at(l.forward_neighbor(x, nu), mu))),
                           G::dagger(f.at(x, nu)));
    }

    template<class G>
    double action(const Field<G> &f, double beta) {
        double sum = 0.;
        for (std::size_t x = 0; x < f.geometry.volume(); ++x)
            for (std::size_t mu = 0; mu < f.geometry.dimension_count(); ++mu)
                for (std::size_t nu = mu + 1; nu < f.geometry.dimension_count(); ++nu)
                    sum += 1. - G::trace(plaquette_matrix(f, x, mu, nu));
        return beta * sum;
    }

    template<class G>
    typename G::Link staple(const Field<G> &f, std::size_t x, std::size_t mu) {
        const auto &l = f.geometry;
        typename G::Link a = G::zero();
        for (std::size_t nu = 0; nu < l.dimension_count(); ++nu) {
            if (mu == nu)
                continue;
            const auto xm = l.forward_neighbor(x, mu), xn = l.forward_neighbor(x, nu);
            const auto xb = l.backward_neighbor(x, nu), xmb = l.backward_neighbor(xm, nu);
            a +=
                    G::multiply(G::multiply(f.at(xm, nu), G::dagger(f.at(xn, mu))), G::dagger(f.at(x, nu)));
            a += G::multiply(G::multiply(G::dagger(f.at(xmb, nu)), G::dagger(f.at(xb, mu))),
                             f.at(xb, nu));
        }
        return a;
    }

    template<class G>
    double action_difference(const Field<G> &f, std::size_t x, std::size_t mu,
                             const typename G::Link &candidate, double beta) {
        const typename G::Link diff = candidate - f.at(x, mu);
        return -beta * G::trace(G::multiply(diff, staple(f, x, mu)));
    }
} // namespace qcd
