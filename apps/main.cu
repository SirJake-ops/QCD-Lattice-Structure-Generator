#include <exception>
#include <filesystem>
#include <iostream>

#include <qcd/config.h>
#include <qcd/network_config.h>

int main(int argc, char *argv[]) {
    const network_config::NetworkConfig config({"First setting"});
    const auto print_setting = [](const network_config::NetworkConfig &first_config) {
        std::cout << first_config << std::endl;
    };

    print_setting(config);

    const std::filesystem::path path_to_toml =
        argc > 1 ? std::filesystem::path{argv[1]} : std::filesystem::path{QCD_DEFAULT_CONFIG_PATH};

    try {
        const auto run_config = toml_config::load_config(path_to_toml);
        std::cout << "Parsed configuration: " << path_to_toml << '\n'
                  << "Gauge group: " << run_config.model_config.gauge_group << '\n';
    } catch (const std::exception &error) {
        std::cerr << "Unable to load configuration '" << path_to_toml << "': " << error.what()
                  << '\n';
        return 1;
    }

    return 0;
}
