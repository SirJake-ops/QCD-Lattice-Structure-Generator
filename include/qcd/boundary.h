#pragma once

#include <string_view>

namespace lattice {

enum class BoundaryCondition {
    periodic,
    open,
    fixed,
};

[[nodiscard]] constexpr std::string_view to_string(const BoundaryCondition condition) noexcept {
    switch (condition) {
    case BoundaryCondition::periodic:
        return "periodic";
    case BoundaryCondition::open:
        return "open";
    case BoundaryCondition::fixed:
        return "fixed";
    }
    return "unknown";
}

} // namespace lattice
