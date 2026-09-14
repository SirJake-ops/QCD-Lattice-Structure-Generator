//
// Created by jacobp on 8/5/26.
//

#include "qcd/lattice.h"
#include <limits>
#include <stdexcept>

lattice::Lattice::Lattice(std::vector<index_type> extents) {
    extents_ = std::move(extents);

    if (extents.empty()) {
        throw std::invalid_argument("Lattice extents must be non-empty");
    }

    index_type temp_volume = 1;
    for (const auto &index : extents) {
        if (index == 0) {
            throw std::invalid_argument("Lattice extents must be non-zero");
        }

        if (temp_volume > (std::numeric_limits<std::size_t>::max() / index)) {
            throw std::overflow_error("Lattice volume is too large");
        }

        temp_volume *= index;
    }

    volume_ = temp_volume;
}

lattice::Lattice::index_type lattice::Lattice::volume() const noexcept { return volume_; }

lattice::Lattice::index_type
lattice::Lattice::site_index(std::span<const index_type> coordinates) const {}
