#pragma once

#include <qcd/action.h>

namespace qcd {
    template<class G>
    double rectangle(const Field<G> &f, std::size_t x, std::size_t mu, std::size_t nu, std::size_t r,
                     std::size_t t) {
        auto product = G::identity();
        const auto forward = [&](std::size_t direction, std::size_t count) {
            for (std::size_t k = 0; k < count; ++k) {
                product = G::multiply(product, f.at(x, direction));
                x = f.geometry.forward_neighbor(x, direction);
            }
        };
        const auto backward = [&](std::size_t direction, std::size_t count) {
            for (std::size_t k = 0; k < count; ++k) {
                x = f.geometry.backward_neighbor(x, direction);
                product = G::multiply(product, G::dagger(f.at(x, direction)));
            }
        };
        forward(mu, r);
        forward(nu, t);
        backward(mu, r);
        backward(nu, t);
        return G::trace(product);
    }

    template<class G>
    double wilson_loop(const Field<G> &f, std::size_t r, std::size_t t) {
        double sum = 0.;
        for (std::size_t x = 0; x < f.geometry.volume(); ++x)
            for (std::size_t mu = 0; mu < 3; ++mu)
                sum += rectangle(f, x, mu, 3, r, t);
        return sum / (3. * static_cast<double>(f.geometry.volume()));
    }

    // Reuse straight transporters across all rectangles. This computes exactly the
    // same observable as rectangle(), with four products per loop after preparation.
    template<class G>
    std::vector<double>
    wilson_loops(const Field<G> &f,
                 const std::vector<std::pair<std::size_t, std::size_t> > &definitions) {
        if (definitions.empty())
            return {};
        const auto &l = f.geometry;
        const auto volume = l.volume();
        std::size_t max_r = 0, max_t = 0;
        for (const auto &[r, t]: definitions) {
            max_r = std::max(max_r, r);
            max_t = std::max(max_t, t);
        }
        struct Paths {
            std::vector<typename G::Link> links;
            std::vector<std::size_t> end;
        };
        std::vector<Paths> paths(4);
        for (std::size_t mu = 0; mu < 4; ++mu) {
            const auto max_length = mu == 3 ? max_t : max_r;
            auto &p = paths[mu];
            p.links.resize((max_length + 1) * volume);
            p.end.resize((max_length + 1) * volume);
            for (std::size_t x = 0; x < volume; ++x) {
                p.links[x] = G::identity();
                p.end[x] = x;
            }
            for (std::size_t length = 1; length <= max_length; ++length)
                for (std::size_t x = 0; x < volume; ++x) {
                    const auto prev = (length - 1) * volume + x, index = length * volume + x;
                    p.links[index] = G::multiply(p.links[prev], f.at(p.end[prev], mu));
                    p.end[index] = l.forward_neighbor(p.end[prev], mu);
                }
        }
        std::vector<double> result;
        for (const auto &[r, t]: definitions) {
            double sum = 0.;
            const auto &tp = paths[3];
            for (std::size_t mu = 0; mu < 3; ++mu) {
                const auto &sp = paths[mu];
                for (std::size_t x = 0; x < volume; ++x) {
                    const auto rx = r * volume + x, tx = t * volume + x;
                    sum += G::trace(G::multiply(
                        G::multiply(G::multiply(sp.links[rx], tp.links[t * volume + sp.end[rx]]),
                                    G::dagger(sp.links[r * volume + tp.end[tx]])),
                        G::dagger(tp.links[tx])));
                }
            }
            result.push_back(sum / (3. * static_cast<double>(volume)));
        }
        return result;
    }

    struct FieldSamples {
        double w{};
        std::vector<double> s, ws;
    };

    // Translation-average the JOINT products, never the product of averaged W and s.
    // x-y plane relative to source, time probe at floor(T/2), one plaquette orientation.
    template<class G>
    FieldSamples field_samples(const Field<G> &f, std::size_t r, std::size_t t, std::size_t probe_mu,
                               std::size_t probe_nu) {
        const auto &l = f.geometry;
        FieldSamples out;
        const auto nx = l.extent(0), ny = l.extent(1);
        out.s.resize(nx * ny);
        out.ws.resize(nx * ny);
        std::vector<double> w(l.volume()), density(l.volume());
        for (std::size_t x = 0; x < l.volume(); ++x) {
            w[x] = rectangle(f, x, 0, 3, r, t);
            out.w += w[x];
            density[x] = 1. - G::trace(plaquette_matrix(f, x, probe_mu, probe_nu));
        }
        const double norm = 1. / static_cast<double>(l.volume());
        out.w *= norm;
        for (std::size_t x = 0; x < l.volume(); ++x) {
            auto midpoint = x;
            for (std::size_t k = 0; k < t / 2; ++k)
                midpoint = l.forward_neighbor(midpoint, 3);
            auto row = midpoint;
            for (std::size_t dy = 0; dy < ny; ++dy) {
                auto probe = row;
                for (std::size_t dx = 0; dx < nx; ++dx) {
                    const auto index = dy * nx + dx;
                    out.s[index] += density[probe] * norm;
                    out.ws[index] += w[x] * density[probe] * norm;
                    probe = l.forward_neighbor(probe, 0);
                }
                row = l.forward_neighbor(row, 1);
            }
        }
        // Exact ensemble symmetries: transverse reflection and source exchange.
        // Plaquette anchors shift by one site when their oriented face is reflected.
        const auto original_s = out.s, original_ws = out.ws;
        const std::size_t sx = (probe_mu == 0 || probe_nu == 0) ? 1 : 0;
        const std::size_t sy = (probe_mu == 1 || probe_nu == 1) ? 1 : 0;
        for (std::size_t dy = 0; dy < ny; ++dy)
            for (std::size_t dx = 0; dx < nx; ++dx) {
                const auto rx = (r + 2 * nx - dx - sx) % nx, ry = (2 * ny - dy - sy) % ny;
                const auto i = dy * nx + dx;
                out.s[i] = .25
                           * (original_s[i] + original_s[dy * nx + rx] + original_s[ry * nx + dx]
                              + original_s[ry * nx + rx]);
                out.ws[i] = .25
                            * (original_ws[i] + original_ws[dy * nx + rx] + original_ws[ry * nx + dx]
                               + original_ws[ry * nx + rx]);
            }
        return out;
    }
} // namespace qcd
