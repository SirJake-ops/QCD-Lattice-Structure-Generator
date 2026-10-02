#ifndef QCD_PREDICTION_TOML_CONFIG_H
#define QCD_PREDICTION_TOML_CONFIG_H

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <iosfwd>
#include <optional>
#include <string>
#include <vector>

#include <qcd/boundary.h>

namespace toml_config {
using BoundaryCondition = lattice::BoundaryCondition;

struct ModelConfig {
    std::string gauge_group;
    std::string action;
    double beta{};
};

struct LatticeConfig {
    std::vector<std::size_t> extents;
    BoundaryCondition boundary_condition{BoundaryCondition::periodic};
    double spacing{};
};

struct SamplingConfig {
    std::size_t chains{};
    std::size_t warmup_sweeps{};
    std::size_t measurement_sweeps{};
    std::size_t sweeps_between_measurements{};
    std::uint64_t seed{};
};

struct UpdateConfig {
    std::string algorithm;
    std::optional<double> proposal_scale;
    std::optional<std::size_t> overrelaxation_sweeps;
};

struct WilsonLoopConfig {
    std::size_t spatial_extent{};
    std::size_t temporal_extent{};
};

struct ObservableConfig {
    bool plaquette{};
    bool polyakov_loop{};
    std::vector<WilsonLoopConfig> wilson_loops;
};

struct ExecutionConfig {
    std::string backend;
    std::string precision;
    std::size_t threads{};
};

struct OutputConfig {
    std::filesystem::path directory;
    std::string format;
    bool save_configurations{};
    std::size_t configuration_interval{};
};

struct RunConfig {
    std::uint32_t schema_version{};
    ModelConfig model_config;
    LatticeConfig lattice_config;
    SamplingConfig sampling_config;
    UpdateConfig update_config;
    ObservableConfig observable_config;
    ExecutionConfig execution_config;
    OutputConfig output_config;
};

RunConfig load_config(const std::filesystem::path &path);
std::ostream &operator<<(std::ostream &os, const RunConfig &config);

} // namespace toml_config

#endif // QCD_PREDICTION_TOML_CONFIG_H
