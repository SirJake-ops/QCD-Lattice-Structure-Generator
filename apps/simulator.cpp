#include <algorithm>
#include <iomanip>
#include <iostream>
#include <qcd/config.h>
#include <qcd/observables.h>
#include <qcd/update.h>
#include <stdexcept>
#include <string>

#ifndef QCD_REVISION
#define QCD_REVISION "unknown"
#endif

namespace {
template <class T> void array(const std::vector<T> &values) {
    std::cout << '[';
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i)
            std::cout << ',';
        std::cout << values[i];
    }
    std::cout << ']';
}
template <class G>
int run(const toml_config::RunConfig &c, std::size_t source_r, std::size_t source_t, std::size_t pm,
        std::size_t pn, bool hot, bool flux) {
    const auto &sampling = c.sampling_config;
    const double scale = c.update_config.proposal_scale.value_or(.5);
    const auto &loops = c.observable_config.wilson_loops;
    std::vector<std::pair<std::size_t, std::size_t>> definitions;
    for (const auto &loop : loops)
        definitions.emplace_back(loop.spatial_extent, loop.temporal_extent);
    std::cout << std::setprecision(17);
    std::cout << "{\"type\":\"header\",\"schema_version\":1,\"revision\":\"" QCD_REVISION
                 "\",\"compiler\":\"" __VERSION__
                 "\",\"rng\":\"mt19937_64/splitmix64\",\"precision\":\"double\",\"loops\":[";
    for (std::size_t i = 0; i < loops.size(); ++i) {
        if (i)
            std::cout << ',';
        std::cout << '[' << loops[i].spatial_extent << ',' << loops[i].temporal_extent << ']';
    }
    std::cout << "]}\n" << std::flush;
    for (std::size_t chain = 0; chain < sampling.chains; ++chain) {
        qcd::Field<G> field(c.lattice_config.extents);
        qcd::rng::RandomStream rng(sampling.seed, chain);
        if (hot)
            field.hot(rng);
        const auto total = sampling.warmup_sweeps
                           + sampling.measurement_sweeps * sampling.sweeps_between_measurements;
        for (std::size_t sweep = 1; sweep <= total; ++sweep) {
            const double accepted = qcd::metropolis(field, rng, c.model_config.beta, scale);
            if (sweep <= sampling.warmup_sweeps) {
                if (sweep % 10 == 0)
                    std::cerr << "warmup " << chain << ' ' << sweep << '\n';
                continue;
            }
            if ((sweep - sampling.warmup_sweeps) % sampling.sweeps_between_measurements)
                continue;
            const auto values = qcd::wilson_loops(field, definitions);
            const double plaquette =
                1. - qcd::action(field, 1.) / (6. * static_cast<double>(field.geometry.volume()));
            std::cout << "{\"type\":\"measurement\",\"chain\":" << chain << ",\"sweep\":" << sweep
                      << ",\"acceptance\":" << accepted << ",\"plaquette\":" << plaquette
                      << ",\"loops\":";
            array(values);
            if (flux) {
                const auto map = qcd::field_samples(field, source_r, source_t, pm, pn);
                std::cout << ",\"w\":" << map.w << ",\"s\":";
                array(map.s);
                std::cout << ",\"ws\":";
                array(map.ws);
            }
            std::cout << "}\n" << std::flush;
        }
    }
    std::cout << "{\"type\":\"complete\"}\n";
    return 0;
}
} // namespace

int main(int argc, char **argv) {
    try {
        if (argc != 2 && argc != 9)
            throw std::invalid_argument("Usage: qcd_simulate CONFIG [source_r source_t probe_mu "
                                        "probe_nu hot(0/1) flux(0/1) reserved(0)]");
        const auto c = toml_config::load_config(argv[1]);
        const auto &e = c.lattice_config.extents;
        if (e.size() != 4 || *std::min_element(e.begin(), e.end()) < 4
            || c.lattice_config.boundary_condition != lattice::BoundaryCondition::periodic
            || c.model_config.action != "wilson" || c.model_config.beta <= 0.
            || c.update_config.algorithm != "metropolis" || c.execution_config.backend != "cpu"
            || c.execution_config.precision != "double" || c.execution_config.threads != 1
            || c.observable_config.polyakov_loop || c.output_config.save_configurations
            || c.update_config.overrelaxation_sweeps.value_or(0) != 0)
            throw std::invalid_argument(
                "Only 4D periodic Wilson, serial double CPU Metropolis is supported; checkpoints "
                "and Polyakov loops are not implemented");
        const std::size_t r = argc == 9 ? std::stoull(argv[2]) : 1;
        const std::size_t t = argc == 9 ? std::stoull(argv[3]) : 2;
        const std::size_t pm = argc == 9 ? std::stoull(argv[4]) : 0;
        const std::size_t pn = argc == 9 ? std::stoull(argv[5]) : 3;
        const bool hot = argc == 9 && std::string(argv[6]) == "1";
        const bool flux = argc == 2 || std::string(argv[7]) == "1";
        if (!r || !t || r > e[0] / 2 || t > e[3] / 2 || pm > 3 || pn > 3 || pm == pn)
            throw std::invalid_argument("Invalid source/probe geometry");
        for (const auto &loop : c.observable_config.wilson_loops)
            if (loop.spatial_extent > *std::min_element(e.begin(), e.begin() + 3) / 2
                || loop.temporal_extent > e[3] / 2)
                throw std::invalid_argument(
                    "Wilson loops must fit within half the periodic extents");
        if (c.observable_config.wilson_loops.empty())
            throw std::invalid_argument("No Wilson loops");
        if (c.model_config.gauge_group == "u1")
            return run<qcd::U1>(c, r, t, pm, pn, hot, flux);
        if (c.model_config.gauge_group == "su3")
            return run<qcd::SU3>(c, r, t, pm, pn, hot, flux);
        throw std::invalid_argument("Gauge group must be u1 or su3");
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
