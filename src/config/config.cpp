#include <qcd/config.h>

#include <toml++/toml.hpp>

#include <cmath>
#include <cstdint>
#include <limits>
#include <ostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace {
std::runtime_error invalid_value(const std::string_view section, const std::string_view key) {
    return std::runtime_error("Missing or invalid configuration value [" + std::string{section}
                              + "]." + std::string{key});
}

const toml::table &required_table(const toml::table &root, const std::string_view key) {
    const auto *table = root[key].as_table();
    if (table == nullptr) {
        throw std::runtime_error("Missing configuration table [" + std::string{key} + "]");
    }
    return *table;
}

template <typename T>
T required_value(const toml::table &table, const std::string_view key,
                 const std::string_view section) {
    const auto value = table[key].value<T>();
    if (!value) {
        throw std::runtime_error("Missing or invalid configuration value [" + std::string{section}
                                 + "]." + std::string{key});
    }
    return *value;
}

std::string required_string(const toml::table &table, const std::string_view key,
                            const std::string_view section) {
    auto value = required_value<std::string>(table, key, section);
    if (value.empty()) {
        throw invalid_value(section, key);
    }
    return value;
}

double required_finite_double(const toml::table &table, const std::string_view key,
                              const std::string_view section, const bool require_positive = false) {
    const double value = required_value<double>(table, key, section);
    if (!std::isfinite(value) || (require_positive && value <= 0.0)) {
        throw invalid_value(section, key);
    }
    return value;
}

std::size_t checked_size(const std::int64_t value, const std::string_view section,
                         const std::string_view key, const bool allow_zero = true) {
    if (value < 0 || (!allow_zero && value == 0)
        || static_cast<std::uint64_t>(value) > std::numeric_limits<std::size_t>::max()) {
        throw std::runtime_error("Missing or invalid configuration value [" + std::string{section}
                                 + "]." + std::string{key});
    }
    return static_cast<std::size_t>(value);
}

std::size_t required_size(const toml::table &table, const std::string_view key,
                          const std::string_view section, const bool allow_zero = true) {
    return checked_size(required_value<std::int64_t>(table, key, section), section, key,
                        allow_zero);
}

toml_config::BoundaryCondition parse_boundary_condition(const toml::table &lattice) {
    const auto value = required_string(lattice, "boundary", "lattice");
    if (value == "periodic") {
        return toml_config::BoundaryCondition::periodic;
    }
    if (value == "open") {
        return toml_config::BoundaryCondition::open;
    }
    if (value == "fixed") {
        return toml_config::BoundaryCondition::fixed;
    }
    throw invalid_value("lattice", "boundary");
}

std::vector<std::size_t> parse_extents(const toml::table &lattice) {
    const auto *values = lattice["extents"].as_array();
    if (values == nullptr || values->empty()) {
        throw invalid_value("lattice", "extents");
    }

    std::vector<std::size_t> extents;
    extents.reserve(values->size());
    for (const auto &node : *values) {
        const auto value = node.value<std::int64_t>();
        if (!value) {
            throw invalid_value("lattice", "extents");
        }
        extents.push_back(checked_size(*value, "lattice", "extents", false));
    }
    return extents;
}

std::vector<toml_config::WilsonLoopConfig> parse_wilson_loops(const toml::table &observables) {
    const auto *values = observables["wilson_loops"].as_array();
    if (values == nullptr) {
        throw invalid_value("observables", "wilson_loops");
    }

    std::vector<toml_config::WilsonLoopConfig> loops;
    loops.reserve(values->size());
    for (const auto &node : *values) {
        const auto *pair = node.as_array();
        if (pair == nullptr || pair->size() != 2) {
            throw invalid_value("observables", "wilson_loops");
        }

        const auto spatial = (*pair)[0].value<std::int64_t>();
        const auto temporal = (*pair)[1].value<std::int64_t>();
        if (!spatial || !temporal) {
            throw invalid_value("observables", "wilson_loops");
        }
        loops.push_back({
            checked_size(*spatial, "observables", "wilson_loops", false),
            checked_size(*temporal, "observables", "wilson_loops", false),
        });
    }
    return loops;
}

template <typename T> struct Field {
    std::string_view name;
    const T &value;
};

template <typename... Fields> void print_fields(std::ostream &os, const Fields &...fields) {
    ((os << fields.name << " = " << fields.value << '\n'), ...);
}

std::ostream &print_extents(std::ostream &os, const std::vector<std::size_t> &extents) {
    os << '[';
    for (std::size_t index = 0; index < extents.size(); ++index) {
        if (index != 0) {
            os << ", ";
        }
        os << extents[index];
    }
    return os << ']';
}
} // namespace

namespace toml_config {
RunConfig load_config(const std::filesystem::path &path) {
    const toml::table root = toml::parse_file(path.string());

    const auto schema_version_value = required_value<std::int64_t>(root, "schema_version", "root");
    if (schema_version_value != 1) {
        throw invalid_value("root", "schema_version");
    }

    const auto &model = required_table(root, "model");
    const auto &lattice = required_table(root, "lattice");
    const auto &sampling = required_table(root, "sampling");
    const auto &update = required_table(root, "update");
    const auto &observables = required_table(root, "observables");
    const auto &execution = required_table(root, "execution");
    const auto &output = required_table(root, "output");

    UpdateConfig update_config{
        .algorithm = required_string(update, "algorithm", "update"),
        .proposal_scale = update["proposal_scale"].value<double>(),
        .overrelaxation_sweeps = std::nullopt,
    };
    if (update_config.proposal_scale
        && (!std::isfinite(*update_config.proposal_scale)
            || *update_config.proposal_scale <= 0.0)) {
        throw invalid_value("update", "proposal_scale");
    }
    if (const auto sweeps = update["overrelaxation_sweeps"].value<std::int64_t>()) {
        update_config.overrelaxation_sweeps =
            checked_size(*sweeps, "update", "overrelaxation_sweeps");
    }

    return RunConfig{
        .schema_version = static_cast<std::uint32_t>(schema_version_value),
        .model_config =
            {
                .gauge_group = required_string(model, "gauge_group", "model"),
                .action = required_string(model, "action", "model"),
                .beta = required_finite_double(model, "beta", "model"),
            },
        .lattice_config =
            {
                .extents = parse_extents(lattice),
                .boundary_condition = parse_boundary_condition(lattice),
                .spacing = required_finite_double(lattice, "spacing", "lattice", true),
            },
        .sampling_config =
            {
                .chains = required_size(sampling, "chains", "sampling", false),
                .warmup_sweeps = required_size(sampling, "warmup_sweeps", "sampling"),
                .measurement_sweeps =
                    required_size(sampling, "measurement_sweeps", "sampling", false),
                .sweeps_between_measurements =
                    required_size(sampling, "sweeps_between_measurements", "sampling", false),
                .seed = static_cast<std::uint64_t>(required_size(sampling, "seed", "sampling")),
            },
        .update_config = std::move(update_config),
        .observable_config =
            {
                .plaquette = required_value<bool>(observables, "plaquette", "observables"),
                .polyakov_loop = required_value<bool>(observables, "polyakov_loop", "observables"),
                .wilson_loops = parse_wilson_loops(observables),
            },
        .execution_config =
            {
                .backend = required_string(execution, "backend", "execution"),
                .precision = required_string(execution, "precision", "execution"),
                .threads = required_size(execution, "threads", "execution", false),
            },
        .output_config =
            {
                .directory = required_string(output, "directory", "output"),
                .format = required_string(output, "format", "output"),
                .save_configurations =
                    required_value<bool>(output, "save_configurations", "output"),
                .configuration_interval =
                    required_size(output, "configuration_interval", "output", false),
            },
    };
}

std::ostream &operator<<(std::ostream &os, const RunConfig &config) {
    const auto original_flags = os.flags();
    os << std::boolalpha;
    os << "schema_version = " << config.schema_version << "\n\n[model]\n";
    print_fields(os, Field{"gauge_group", config.model_config.gauge_group},
                 Field{"action", config.model_config.action},
                 Field{"beta", config.model_config.beta});

    os << "\n[lattice]\nextents = ";
    print_extents(os, config.lattice_config.extents) << '\n';
    print_fields(os,
                 Field{"boundary", lattice::to_string(config.lattice_config.boundary_condition)},
                 Field{"spacing", config.lattice_config.spacing});

    os << "\n[sampling]\n";
    print_fields(
        os, Field{"chains", config.sampling_config.chains},
        Field{"warmup_sweeps", config.sampling_config.warmup_sweeps},
        Field{"measurement_sweeps", config.sampling_config.measurement_sweeps},
        Field{"sweeps_between_measurements", config.sampling_config.sweeps_between_measurements},
        Field{"seed", config.sampling_config.seed});

    os << "\n[update]\nalgorithm = " << config.update_config.algorithm << '\n';
    if (config.update_config.proposal_scale) {
        os << "proposal_scale = " << *config.update_config.proposal_scale << '\n';
    }
    if (config.update_config.overrelaxation_sweeps) {
        os << "overrelaxation_sweeps = " << *config.update_config.overrelaxation_sweeps << '\n';
    }

    os << "\n[observables]\n";
    print_fields(os, Field{"plaquette", config.observable_config.plaquette},
                 Field{"polyakov_loop", config.observable_config.polyakov_loop});
    os << "wilson_loops = [";
    for (std::size_t index = 0; index < config.observable_config.wilson_loops.size(); ++index) {
        if (index != 0) {
            os << ", ";
        }
        const auto &loop = config.observable_config.wilson_loops[index];
        os << '[' << loop.spatial_extent << ", " << loop.temporal_extent << ']';
    }
    os << "]\n\n[execution]\n";
    print_fields(os, Field{"backend", config.execution_config.backend},
                 Field{"precision", config.execution_config.precision},
                 Field{"threads", config.execution_config.threads});

    os << "\n[output]\n";
    print_fields(os, Field{"directory", config.output_config.directory.string()},
                 Field{"format", config.output_config.format},
                 Field{"save_configurations", config.output_config.save_configurations},
                 Field{"configuration_interval", config.output_config.configuration_interval});
    os.flags(original_flags);
    return os;
}

} // namespace toml_config
