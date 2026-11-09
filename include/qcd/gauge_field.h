#pragma once

#include "gauge_group.h"
#include "lattice.h"
#include <Eigen/Dense>
#include <stdexcept>
#include <utility>
#include <vector>

namespace gauge_field {

using Su3Matrix = Eigen::Matrix3cd;

} // namespace gauge_field

namespace qcd {
template <class Group> class Field {
  public:
    using Link = typename Group::Link;
    explicit Field(std::vector<std::size_t> extents)
        : geometry(std::move(extents)), links(geometry.link_count(), Group::identity()) {}
    lattice::Lattice geometry;
    std::vector<Link> links;
    Link &at(std::size_t x, std::size_t mu) { return links.at(geometry.link_index(x, mu)); }
    const Link &at(std::size_t x, std::size_t mu) const {
        return links.at(geometry.link_index(x, mu));
    }
    void hot(rng::RandomStream &r) {
        for (auto &u : links)
            u = Group::hot(r);
    }
    void transform(const std::vector<Link> &g) {
        if (g.size() != geometry.volume())
            throw std::invalid_argument("Gauge transformation size");
        for (std::size_t x = 0; x < geometry.volume(); ++x)
            for (std::size_t mu = 0; mu < geometry.dimension_count(); ++mu)
                at(x, mu) = Group::multiply(Group::multiply(g[x], at(x, mu)),
                                            Group::dagger(g[geometry.forward_neighbor(x, mu)]));
    }
};
} // namespace qcd

namespace gauge_field {
using GaugeField = qcd::Field<qcd::SU3>;
}
