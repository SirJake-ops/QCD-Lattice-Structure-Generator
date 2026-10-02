#include "qcd/lattice.h"

#include <limits>
#include <stdexcept>
#include <utility>

lattice::Lattice::Lattice(std::vector<index_type> extents) : extents_(std::move(extents)) {
    if (extents_.empty()) {
        throw std::invalid_argument("Lattice extents must be non-empty");
    }

    strides_.resize(extents_.size());
    index_type volume = 1;
    for (index_type direction = 0; direction < extents_.size(); ++direction) {
        const index_type current_extent = extents_[direction];
        if (current_extent == 0) {
            throw std::invalid_argument("Lattice extents must be non-zero");
        }

        strides_[direction] = volume;
        if (volume > (std::numeric_limits<index_type>::max() / current_extent)) {
            throw std::overflow_error("Lattice volume is too large");
        }
        volume *= current_extent;
    }

    if (volume > (std::numeric_limits<index_type>::max() / extents_.size())) {
        throw std::overflow_error("Lattice link count is too large");
    }
    volume_ = volume;
}

lattice::Lattice::index_type lattice::Lattice::dimension_count() const noexcept {
    return extents_.size();
}

lattice::Lattice::index_type lattice::Lattice::extent(const index_type direction) const {
    if (direction >= dimension_count()) {
        throw std::out_of_range("Lattice direction is out of range");
    }
    return extents_[direction];
}

std::span<const lattice::Lattice::index_type> lattice::Lattice::extents() const noexcept {
    return extents_;
}

lattice::Lattice::index_type lattice::Lattice::volume() const noexcept { return volume_; }

lattice::Lattice::index_type lattice::Lattice::link_count() const noexcept {
    return volume_ * dimension_count();
}

lattice::Lattice::index_type
lattice::Lattice::site_index(const std::span<const index_type> coordinates) const {
    if (coordinates.size() != dimension_count()) {
        throw std::invalid_argument("Coordinate dimensionality does not match the lattice");
    }

    index_type site = 0;
    for (index_type direction = 0; direction < dimension_count(); ++direction) {
        if (coordinates[direction] >= extents_[direction]) {
            throw std::out_of_range("Lattice coordinate is out of range");
        }
        site += coordinates[direction] * strides_[direction];
    }
    return site;
}

lattice::Lattice::coordinate_type lattice::Lattice::coordinate(const index_type site) const {
    if (site >= volume_) {
        throw std::out_of_range("Lattice site is out of range");
    }

    coordinate_type result(dimension_count());
    for (index_type direction = 0; direction < dimension_count(); ++direction) {
        result[direction] = (site / strides_[direction]) % extents_[direction];
    }
    return result;
}

lattice::Lattice::index_type lattice::Lattice::forward_neighbor(const index_type site,
                                                                const index_type direction) const {
    if (site >= volume_) {
        throw std::out_of_range("Lattice site is out of range");
    }
    const index_type direction_extent = extent(direction);
    const index_type stride = strides_[direction];
    const index_type component = (site / stride) % direction_extent;
    return component + 1 == direction_extent ? site - (direction_extent - 1) * stride
                                             : site + stride;
}

lattice::Lattice::index_type lattice::Lattice::backward_neighbor(const index_type site,
                                                                 const index_type direction) const {
    if (site >= volume_) {
        throw std::out_of_range("Lattice site is out of range");
    }
    const index_type direction_extent = extent(direction);
    const index_type stride = strides_[direction];
    const index_type component = (site / stride) % direction_extent;
    return component == 0 ? site + (direction_extent - 1) * stride : site - stride;
}

lattice::Lattice::index_type lattice::Lattice::link_index(const index_type site,
                                                          const index_type direction) const {
    if (site >= volume_) {
        throw std::out_of_range("Lattice site is out of range");
    }
    static_cast<void>(extent(direction));
    return site * dimension_count() + direction;
}
