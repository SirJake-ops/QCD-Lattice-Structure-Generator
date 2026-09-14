#pragma once

//
// Created by jacobp on 8/5/26.
//
//

#include "lattice.h"
#include <Eigen/Dense>
#include <vector>

namespace gauge_field {

// A general complex matrix; SU(3) constraints are enforced by the gauge algorithms.
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
