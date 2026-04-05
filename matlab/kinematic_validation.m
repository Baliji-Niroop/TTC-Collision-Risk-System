% kinematic_validation.m
% Validates synthetic TTC telemetry scenarios from the system.

clear; clc; close all;

% Load dataset
filename = '../dataset/synthetic_ttc_validation.csv';
if exist(filename, 'file')
    df = readtable(filename);
else
    disp('Validation dataset not found.');
    disp(['Expected at: ', filename]);
    return;
end

% Separate scenarios
scenarios = unique(df.scenario);
disp(['Found ', num2str(length(scenarios)), ' scenarios.']);

% Prepare 4-panel plot
figure('Name', 'Kinematic Validation', 'Position', [100, 100, 1000, 800]);

% Panel 1: Fast Collision scenario vs TTC
ax1 = subplot(2, 2, 1);
idx_fc = strcmp(df.scenario, 'fast_collision');
if any(idx_fc)
    plot(df.timestamp_ms(idx_fc), df.distance_cm(idx_fc) / 100, 'LineWidth', 2);
    hold on;
    plot(df.timestamp_ms(idx_fc), df.ttc_basic(idx_fc), 'r--', 'LineWidth', 2);
    plot(df.timestamp_ms(idx_fc), df.ttc_ext(idx_fc), 'g-.', 'LineWidth', 2);
    legend('Distance (m)', 'TTC_B (s)', 'TTC_E (s)');
    title('Fast Collision Kinematics');
    grid on;
end

% Panel 2: Sudden Braking scenario
ax2 = subplot(2, 2, 2);
idx_sb = strcmp(df.scenario, 'sudden_braking');
if any(idx_sb)
    plot(df.timestamp_ms(idx_sb), df.speed_kmh(idx_sb), 'LineWidth', 2);
    hold on;
    plot(df.timestamp_ms(idx_sb), df.ttc_basic(idx_sb), 'r-', 'LineWidth', 1.5);
    legend('Speed (km/h)', 'TTC_B (s)');
    title('Sudden Braking Kinematics');
    grid on;
end

% Panel 3: Confidence vs Noise
ax3 = subplot(2, 2, 3);
idx_ns = strcmp(df.scenario, 'noisy_sensor');
if any(idx_ns)
    noise_err = abs(df.distance_cm(idx_ns) - df.latent_distance_cm(idx_ns));
    scatter(noise_err, df.confidence(idx_ns), 'filled');
    xlabel('Measurement Error (cm)');
    ylabel('Confidence');
    title('Noise Suppression & Confidence');
    grid on;
end

% Panel 4: Risk Distribution
ax4 = subplot(2, 2, 4);
h = histogram(df.ground_truth_risk_class);
h.BinEdges = [-0.5, 0.5, 1.5, 2.5];
title('Global Risk Class Distribution');
set(gca, 'XTick', [0, 1, 2], 'XTickLabel', {'SAFE', 'WARN', 'CRIT'});
grid on;

% RMS Error check for TTC (Optional / after-the-fact validation)
% This requires truth values, which we recalculate here for TTC_B:
truth_ttc = (df.latent_distance_cm / 100.0) ./ max(df.latent_speed_kmh / 3.6, 0.1);
actual_ttc = (df.distance_cm / 100.0) ./ max(df.speed_kmh / 3.6, 0.1);

valid = ~isnan(truth_ttc) & ~isinf(truth_ttc) & ~isnan(actual_ttc) & ~isinf(actual_ttc);
mse = mean((actual_ttc(valid) - truth_ttc(valid)).^2);
rmse = sqrt(mse);

disp(['Validation Complete. Global TTC RMSE: ', num2str(rmse), ' seconds.']);
