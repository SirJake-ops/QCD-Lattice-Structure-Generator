#include <array>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>

#include <gtest/gtest.h>

#include <qcd/config.h>

namespace {

std::filesystem::path config_path(const std::string_view filename) {
    return std::filesystem::path{QCD_CONFIG_DIR} / filename;
}

std::string read_file(const std::filesystem::path &path) {
    std::ifstream input(path);
    if (!input) {
        throw std::runtime_error("Unable to read test input: " + path.string());
    }
    return {std::istreambuf_iterator<char>{input}, std::istreambuf_iterator<char>{}};
}

std::filesystem::path write_modified_config(const std::string_view filename,
                                            const std::string_view original,
                                            const std::string_view replacement) {
    std::string contents = read_file(config_path("small-test.toml"));
    const auto position = contents.find(original);
    if (position == std::string::npos) {
        throw std::runtime_error("Test fixture text was not found");
    }
    contents.replace(position, original.size(), replacement);

    const auto path = std::filesystem::path{testing::TempDir()} / filename;
    std::ofstream output(path);
    output << contents;
    if (!output) {
        throw std::runtime_error("Unable to write test input: " + path.string());
    }
    return path;
}

TEST(ConfigTest, LoadsEveryExampleConfiguration) {
    constexpr std::array config_files{
        "default.toml",
        "small-test.toml",
        "example-su3.toml",
    };

    for (const std::string_view filename : config_files) {
        EXPECT_NO_THROW(static_cast<void>(toml_config::load_config(config_path(filename))))
            << "Could not load " << filename;
    }
}

TEST(ConfigTest, LoadsTypedDefaultConfiguration) {
    const auto config = toml_config::load_config(config_path("default.toml"));

    EXPECT_EQ(config.schema_version, 1U);
    EXPECT_EQ(config.model_config.gauge_group, "u1");
    EXPECT_EQ(config.model_config.action, "wilson");
    EXPECT_DOUBLE_EQ(config.model_config.beta, 1.0);
    EXPECT_EQ(config.lattice_config.extents.size(), 4U);
    EXPECT_EQ(config.lattice_config.boundary_condition, toml_config::BoundaryCondition::periodic);
    EXPECT_EQ(config.sampling_config.seed, 12345U);
    ASSERT_TRUE(config.update_config.proposal_scale.has_value());
    EXPECT_DOUBLE_EQ(*config.update_config.proposal_scale, 0.25);
    EXPECT_EQ(config.observable_config.wilson_loops.size(), 3U);
    EXPECT_EQ(config.output_config.directory, "results/default");
}

TEST(ConfigTest, PrintsEveryResolvedSection) {
    const auto config = toml_config::load_config(config_path("small-test.toml"));
    std::ostringstream output;
    output << config;

    for (const std::string_view section : {"[model]", "[lattice]", "[sampling]", "[update]",
                                           "[observables]", "[execution]", "[output]"}) {
        EXPECT_NE(output.str().find(section), std::string::npos) << section;
    }
    EXPECT_NE(output.str().find("extents = [4, 4, 4, 4]"), std::string::npos);
    EXPECT_NE(output.str().find("wilson_loops = [[1, 1]]"), std::string::npos);
}

TEST(ConfigTest, RejectsUnsupportedSchema) {
    const auto path = write_modified_config("qcd-unsupported-schema.toml", "schema_version = 1",
                                            "schema_version = 2");
    EXPECT_THROW(static_cast<void>(toml_config::load_config(path)), std::runtime_error);
}

TEST(ConfigTest, RejectsMissingRequiredTable) {
    const auto path = write_modified_config("qcd-missing-table.toml", "[sampling]", "[renamed]");
    EXPECT_THROW(static_cast<void>(toml_config::load_config(path)), std::runtime_error);
}

TEST(ConfigTest, RejectsInvalidExtents) {
    const auto path = write_modified_config("qcd-zero-extent.toml", "extents = [4, 4, 4, 4]",
                                            "extents = [4, 0, 4, 4]");
    EXPECT_THROW(static_cast<void>(toml_config::load_config(path)), std::runtime_error);
}

TEST(ConfigTest, RejectsUnknownBoundaryCondition) {
    const auto path = write_modified_config("qcd-invalid-boundary.toml", "boundary = \"periodic\"",
                                            "boundary = \"wrapped\"");
    EXPECT_THROW(static_cast<void>(toml_config::load_config(path)), std::runtime_error);
}

TEST(ConfigTest, RejectsNonPositiveSpacing) {
    const auto path =
        write_modified_config("qcd-invalid-spacing.toml", "spacing = 1.0", "spacing = 0.0");
    EXPECT_THROW(static_cast<void>(toml_config::load_config(path)), std::runtime_error);
}

TEST(ConfigTest, RejectsNonPositiveProposalScale) {
    const auto path = write_modified_config("qcd-invalid-proposal.toml", "proposal_scale = 0.25",
                                            "proposal_scale = 0.0");
    EXPECT_THROW(static_cast<void>(toml_config::load_config(path)), std::runtime_error);
}

} // namespace
