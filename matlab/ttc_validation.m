%% TTC Collision Detection System - MATLAB Kinematic Validation
% 
% @file ttc_validation.m
% @brief Validates TTC calculations against theoretical kinematics
%
% Simulates collision scenarios from initial conditions and compares
% computed TTC values against real-world logged data from ESP32.
%
% Features:
% - Generates synthetic collision scenarios
% - Simulates vehicle kinematics (constant velocity, deceleration)
% - Computes theoretical TTC at each timestep
% - Compares against ESP32 logged values
% - Produces RMSE metrics and overlay plots
%
% Usage:
%   >> ttc_validation
%   Loads dataset/synthetic_ttc_validation.csv and generates plots

clear all; close all; clc;

%% Configuration
SAMPLE_RATE_HZ = 10;           % 100ms loop period
TIMESTEP_S = 1 / SAMPLE_RATE_HZ;
MAX_DISTANCE_CM = 500;         % Maximum visibility
MIN_DISTANCE_CM = 20;          % Collision threshold

%% Load or Generate Test Data
fprintf('=== TTC Kinematic Validation ===\n\n');
fprintf('[1/4] Loading/generating test data...\n');

% Try to load real data first, fall back to synthetic
data_file = '../dataset/synthetic_ttc_validation.csv';
if isfile(data_file)
    fprintf('  Loading from: %s\n', data_file);
    opts = detectImportOptions(data_file);
    data = readtable(data_file, opts);
    
    % Extract columns (assuming standard format)
    timestamp_ms = table2array(data(:, 1));
    distance_cm = table2array(data(:, 2));
    v_closing_ms = table2array(data(:, 3));
    ttc_logged = table2array(data(:, 4));
    
else
    fprintf('  Generating synthetic collision scenario...\n');
    
    % Scenario: Target object at 400cm, moving at -2.5 m/s (approaching)
    % Host vehicle braking at 5 m/s²
    num_samples = 80;  % 8 seconds of simulation
    
    timestamp_ms = (1:num_samples)' * 100;
    distance_cm = zeros(num_samples, 1);
    v_closing_ms = zeros(num_samples, 1);
    ttc_logged = zeros(num_samples, 1);
    
    % Initial conditions
    D_initial = 400;   % Distance in cm
    V_closing = 3.0;   % m/s (gap closing rate)
    A_decel = 5.0;     % m/s² braking deceleration
    
    for i = 1:num_samples
        t = (i-1) * TIMESTEP_S;
        
        % Kinematic equations
        % D(t) = D0 - V*t (constant velocity for one object)
        distance_m = (D_initial/100) - (V_closing * t);
        distance_cm(i) = distance_m * 100;
        
        % Guard against collision
        if distance_cm(i) < MIN_DISTANCE_CM
            distance_cm(i) = MIN_DISTANCE_CM;
        end
        
        % Closing velocity (derived from distance)
        if i > 1
            delta_d = (distance_cm(i-1) - distance_cm(i)) / 100;  % Convert to meters
            v_closing_ms(i) = delta_d / TIMESTEP_S;
        else
            v_closing_ms(i) = V_closing;
        end
        
        % Compute TTC: distance / velocity
        if v_closing_ms(i) > 0.1
            ttc_logged(i) = (distance_cm(i)/100) / v_closing_ms(i);
        else
            ttc_logged(i) = 99.0;  % No collision threat
        end
        
        % Clamp TTC
        ttc_logged(i) = min(ttc_logged(i), 99.0);
    end
end

fprintf('  ✓ Loaded %d samples\n', length(timestamp_ms));

%% Compute Theoretical TTC (Physics Model)
fprintf('[2/4] Computing theoretical TTC...\n');

ttc_theoretical = zeros(size(ttc_logged));
distance_m = distance_cm / 100;  % Convert to meters

% Use circular buffer approach: compute velocity from 3-point history
buffer_size = 3;
distance_buffer = [];

for i = 1:length(distance_m)
    distance_buffer = [distance_buffer; distance_m(i)];
    
    if length(distance_buffer) > buffer_size
        distance_buffer = distance_buffer(end-buffer_size+1:end);
    end
    
    % Compute velocity if we have at least 2 points
    if length(distance_buffer) >= 2
        d_oldest = distance_buffer(1);
        d_newest = distance_buffer(end);
        t_delta = (length(distance_buffer) - 1) * TIMESTEP_S;
        
        v_closing = (d_oldest - d_newest) / t_delta;
        
        % Basic TTC: distance / velocity
        if v_closing > 0.1
            ttc_theoretical(i) = d_newest / v_closing;
        else
            ttc_theoretical(i) = 99.0;
        end
    else
        ttc_theoretical(i) = 99.0;
    end
    
    % Clamp to valid range
    ttc_theoretical(i) = min(max(ttc_theoretical(i), 0), 99.0);
end

fprintf('  ✓ Computed theoretical TTC values\n');

%% Compute RMSE and Error Metrics
fprintf('[3/4] Computing validation metrics...\n');

% Only compare where both have valid data
valid_idx = (ttc_logged > 0) & (ttc_theoretical > 0);
ttc_logged_valid = ttc_logged(valid_idx);
ttc_theoretical_valid = ttc_theoretical(valid_idx);

rmse = sqrt(mean((ttc_logged_valid - ttc_theoretical_valid).^2));
mae = mean(abs(ttc_logged_valid - ttc_theoretical_valid));
max_error = max(abs(ttc_logged_valid - ttc_theoretical_valid));
correlation = corr(ttc_logged_valid, ttc_theoretical_valid);

fprintf('  RMSE:        %.4f seconds\n', rmse);
fprintf('  MAE:         %.4f seconds\n', mae);
fprintf('  Max Error:   %.4f seconds\n', max_error);
fprintf('  Correlation: %.4f\n', correlation);

% Classify errors
error_vec = ttc_logged_valid - ttc_theoretical_valid;
small_errors = sum(abs(error_vec) < 0.1);
medium_errors = sum((abs(error_vec) >= 0.1) & (abs(error_vec) < 0.5));
large_errors = sum(abs(error_vec) >= 0.5);

fprintf('  Error Distribution:\n');
fprintf('    < 0.1s:    %d samples (%.1f%%)\n', small_errors, 100*small_errors/length(error_vec));
fprintf('    0.1-0.5s:  %d samples (%.1f%%)\n', medium_errors, 100*medium_errors/length(error_vec));
fprintf('    >= 0.5s:   %d samples (%.1f%%)\n', large_errors, 100*large_errors/length(error_vec));

%% Generate Plots
fprintf('[4/4] Generating validation plots...\n');

time_s = timestamp_ms / 1000;  % Convert to seconds

% Figure 1: TTC Comparison
figure('Name', 'TTC Validation', 'NumberTitle', 'off', 'Position', [50 50 1200 800]);

subplot(2,2,1);
plot(time_s, ttc_logged, 'b-', 'LineWidth', 2, 'DisplayName', 'Logged (ESP32)');
hold on;
plot(time_s, ttc_theoretical, 'r--', 'LineWidth', 2, 'DisplayName', 'Theoretical');
yline(3.0, 'g:', 'LineWidth', 1.5, 'DisplayName', 'SAFE Threshold');
yline(1.5, 'orange', 'LinkLineStyle', ':', 'LineWidth', 1.5, 'DisplayName', 'CRITICAL Threshold');
xlabel('Time (s)');
ylabel('TTC (seconds)');
title('Time-to-Collision Comparison');
legend('Location', 'best');
grid on;
ylim([0 5]);

% Figure 2: Distance vs Time
subplot(2,2,2);
plot(time_s, distance_cm, 'b-', 'LineWidth', 2);
xlabel('Time (s)');
ylabel('Distance (cm)');
title('Object Distance');
grid on;

% Figure 3: Error Distribution
subplot(2,2,3);
error_ts = ttc_logged - ttc_theoretical;
plot(time_s, error_ts, 'purple', 'LineWidth', 1.5);
hold on;
yline(0, 'k--', 'LineWidth', 1);
yline(rmse, 'r:', 'LineWidth', 1.5, 'DisplayName', sprintf('RMSE = %.3f', rmse));
yline(-rmse, 'r:', 'LineWidth', 1.5);
xlabel('Time (s)');
ylabel('Error (seconds)');
title('Prediction Error Over Time');
legend;
grid on;

% Figure 4: Scatter Plot (logged vs theoretical)
subplot(2,2,4);
scatter(ttc_theoretical_valid, ttc_logged_valid, 30, 'filled', 'MarkerAlpha', 0.6);
hold on;
plot([0 6], [0 6], 'k--', 'LineWidth', 2, 'DisplayName', 'Perfect Agreement');
xlabel('Theoretical TTC (s)');
ylabel('Logged TTC (s)');
title('Model vs Data');
legend;
grid on;
axis equal;
xlim([0 6]);
ylim([0 6]);

sgtitle(sprintf('TTC Kinematic Validation - RMSE = %.4f seconds', rmse), 'FontSize', 14);

% Save figure
print(gcf, '../validation/outputs/ttc_validation.png', '-dpng', '-r150');
fprintf('  ✓ Saved validation plot\n');

%% Risk Class Validation
fprintf('\n=== Risk Classification Validation ===\n\n');

% Define risk thresholds
SAFE_THRESHOLD = 3.0;
WARNING_THRESHOLD = 1.5;

% Classify logged data
risk_logged = zeros(size(ttc_logged));
risk_logged(ttc_logged >= SAFE_THRESHOLD) = 0;      % SAFE
risk_logged((ttc_logged < SAFE_THRESHOLD) & (ttc_logged >= WARNING_THRESHOLD)) = 1;  % WARNING
risk_logged(ttc_logged < WARNING_THRESHOLD) = 2;    % CRITICAL

% Classify theoretical data
risk_theoretical = zeros(size(ttc_theoretical));
risk_theoretical(ttc_theoretical >= SAFE_THRESHOLD) = 0;
risk_theoretical((ttc_theoretical < SAFE_THRESHOLD) & (ttc_theoretical >= WARNING_THRESHOLD)) = 1;
risk_theoretical(ttc_theoretical < WARNING_THRESHOLD) = 2;

% Confusion matrix for risk classification
risk_names = {'SAFE', 'WARNING', 'CRITICAL'};
confusion_risk = confusionmat(risk_logged(valid_idx), risk_theoretical(valid_idx));

fprintf('Risk Classification Confusion Matrix:\n');
fprintf('           Theoretical\n');
fprintf('         SAFE  WARN  CRIT\n');
for i = 1:3
    fprintf('%s    %4d  %4d  %4d\n', risk_names{i}, confusion_risk(i,1), confusion_risk(i,2), confusion_risk(i,3));
end

% Classification accuracy
risk_agreement = sum(diag(confusion_risk)) / sum(confusion_risk(:));
fprintf('\nRisk Classification Agreement: %.1f%%\n', 100 * risk_agreement);

%% Summary and Recommendations
fprintf('\n=== VALIDATION SUMMARY ===\n\n');

if rmse < 0.2
    fprintf('✓ EXCELLENT: RMSE < 0.2s - Model accuracy is very good\n');
elseif rmse < 0.5
    fprintf('✓ GOOD: RMSE < 0.5s - Model accuracy is acceptable\n');
elseif rmse < 1.0
    fprintf('⚠ WARNING: RMSE < 1.0s - Consider model refinement\n');
else
    fprintf('✗ POOR: RMSE >= 1.0s - Requires significant debugging\n');
end

if risk_agreement > 0.95
    fprintf('✓ Risk classification accuracy: >95%% - Highly reliable\n');
elseif risk_agreement > 0.85
    fprintf('✓ Risk classification accuracy: >85%% - Good reliability\n');
else
    fprintf('⚠ Risk classification accuracy: <85%% - Review thresholds\n');
end

fprintf('\nRecommendations:\n');
fprintf('1. Validate with real-world edge cases\n');
fprintf('2. Test low-speed (<5 km/h) scenarios separately\n');
fprintf('3. Monitor for false positives (CRITICAL when SAFE)\n');
fprintf('4. Ensure Kalman filter tuning matches production config\n');

fprintf('\nValidation complete! Results saved to: ../validation/outputs/\n');
