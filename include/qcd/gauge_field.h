#pragma once

#include "lattice.h"
#include <Eigen/Dense>
#include <vector>

namespace gauge_field {

using Su3Matrix = Eigen::Matrix3cd;

class GaugeField {

  public:
    enum class Layout { AoS, SoA };

  private:
    lattice::Lattice geom_;
    Layout layout_;
    std::vector<Su3Matrix> data_;
};
} // namespace gauge_field
