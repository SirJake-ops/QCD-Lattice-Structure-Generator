//
// Created by jacobp on 8/5/26.
//

#ifndef QCD_PREDICTION_NETWORK_CONFIG_H
#define QCD_PREDICTION_NETWORK_CONFIG_H

#include <ostream>
#include <string>


namespace network_config {
    struct Settings {
        std::string name;
    };

    class NetworkConfig {
    public:
        explicit NetworkConfig(const Settings& settings) : _settings(settings) {}
        NetworkConfig(const NetworkConfig&) = default;
        NetworkConfig(NetworkConfig&&) = default;
        NetworkConfig& operator=(const NetworkConfig&) = default;

        ~NetworkConfig() = default;

        friend std::ostream& operator<<(std::ostream& os, const NetworkConfig& config) {
            os << config._settings.name << std::endl;
            return os;
        }

    private:
        Settings _settings;
    };
}


#endif // QCD_PREDICTION_NETWORK_CONFIG_H
