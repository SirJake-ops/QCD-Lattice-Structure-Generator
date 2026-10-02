#pragma once

#include <cstddef>
#include <span>
#include <vector>

namespace lattice {

class Lattice {
  public:
    using index_type = std::size_t;
    using coordinate_type = std::vector<index_type>;

    explicit Lattice(std::vector<index_type> extents);

    [[nodiscard]] index_type dimension_count() const noexcept;
    [[nodiscard]] index_type extent(index_type direction) const;
    [[nodiscard]] std::span<const index_type> extents() const noexcept;
    [[nodiscard]] index_type volume() const noexcept;
    [[nodiscard]] index_type link_count() const noexcept;
    [[nodiscard]] index_type site_index(std::span<const index_type> coordinates) const;

    [[nodiscard]] coordinate_type coordinate(index_type site) const;

    [[nodiscard]] index_type forward_neighbor(index_type site, index_type direction) const;
    [[nodiscard]] index_type backward_neighbor(index_type site, index_type direction) const;
    [[nodiscard]] index_type link_index(index_type site, index_type direction) const;

  private:
    std::vector<index_type> extents_{};
    std::vector<index_type> strides_{};
    index_type volume_{};
};

} // namespace lattice
