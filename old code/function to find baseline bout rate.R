# 假设这些参数和数据已经定义
params <- c(fit_Sibs_all[1] / 1000, meanposture_Control, boutduration_Control, angVelCoeffs_Control,
            NetRotFit_Control, NetRotMean_Control, NetRotSD_Control, NetRotRsq_Control,
            AngAcc_Fit_C, NetAngAccMean_C, NetAngAccSD_C, AccRsq_C, sliceAngAccSD_C, passive_AngAcc_Control)

# 目标数据
targetIEIdist <- targetIEIdist # 你的目标IEI分布数据

# 初始参数
coeffInit <- coeffInit # 你的初始参数

# 拟合选项
opts <- opts # 你的拟合选项

# 定义拟合函数
fit_function <- function(params, binit) {
  KRH_IEI_fitparameters_2024(binit, params)
}

# 使用nls进行非线性拟合
nls_model <- nls(targetIEIdist ~ fit_function(params, binit),
                 start = list(binit = coeffInit),
                 algorithm = "port", control = opts)

# 提取拟合系数
coeffsIEI <- coef(nls_model)

# 计算参数的置信区间
library(MASS)
coeffsIEI_CI <- confint(nls_model)


#KRH_IEI_fitparameters_2024 <- function(binit, coeffs) {
  # Some parameters
  Model_Duration <- 3000 # duration of simulation in sec
  num_Iterations <- 5 # how many times is the simulation run?
  num_Bins <- 160 # number of bins for output (probability distribution of IEIs)
  samplerate <- 40 # in Hz
  SwimBout_Duration <- round(coeffs[3] * samplerate) # duration of swim bouts in samples (how far is simulation advanced upon bout initiation? empirical match to nefma 7dpf control)
  t_offset <- 10 # absolute refractory period for bout initiation, from initiation of previous bout, in samples.
  pref_posture <- coeffs[2]
  abs_max_pitchchg <- 60 # bouts can't correct more than this ceiling degree
  linearportion_pitchchg <- c(-30, 40)
  pitchsensitivity <- coeffs[1]
  passive_AngAcc <- coeffs[19] # median angular acceleration experienced during IEIs
  passiveAccSD <- 3 # empirically this matches the distribution best for all conditions
  
  # initialized variables that are being optimized
  tEnd <- binit[2]
  
  # this is the gain of the pre-bout pitch with the total rotation from post
  # bout to pre-bout
  Net_Bout_Rotation_Fit <- c(coeffs[8], coeffs[9])
  Net_Bout_Rotation_Mean <- coeffs[10]
  Net_Bout_Rotation_SD <- coeffs[11]
  NetBoutRsq <- coeffs[12]
  
  # this is the gain of angular acceleration correction
  AngAcc_Fit <- c(coeffs[13], coeffs[14])
  Net_Bout_AngAcc_Mean <- coeffs[15]
  Net_Bout_AngAcc_SD <- coeffs[16]
  AngAcc_Rsquared <- coeffs[17]
  SliceAngAcc_SD <- coeffs[18]
  
  # angular velocity coefficients
  m_up <- coeffs[5]
  m_down <- coeffs[6]
  center_angVel <- coeffs[7]
  basalboutrate <- binit[1] # coeffs[4]; # basal bout rate based from angular velocity fig
  
  # switches
  Prior_Short <- 1
  AngVel_Correction_Switch <- 1
  Pitch_Correction_Switch <- 1
  
  # initialize some variables 
  All_IEI <- c()
  All_PitchIEIs <- c()
  
  # Simulate swimming
  for (model_Iteration in 1:num_Iterations) {
    # Initialize variables for appending simulated bout properties
    Net_Bout_AngAcc <- c()
    Net_Bout_Rotation <- c()
    Pre_Bout_Pitch <- c()
    Pre_Bout_AngVel <- c()
    
    # Initialize pitch and angular velocity variables (each simulation begins at horizontal and with no angular velocity)
    Pitch <- sample(-90:90, 1)
    AngVel <- 0
    
    # The simulation advances time-steps using a while loop
    t <- 1 # 't' is the time index
    
    # The simulation begins as though a bout was just terminated, required for determining time-variant bout initiation
    Bout_Index <- -1
    
    # advance until the simulation reaches the set duration
    while (t < (Model_Duration * samplerate)) {
      t <- t + 1
      
      # Each time-step, angular acceleration is used to calculate new angular velocity
      acc <- rnorm(1, passive_AngAcc, passiveAccSD)
      AngVel[t] <- AngVel[t-1] + cos(Pitch[t-1] * pi / 180) * acc / samplerate
      
      # Angular velocity is used to calculate new pitch
      Pitch[t] <- Pitch[t-1] + AngVel[t] / samplerate
      
      # limit pitches to +/- 180 deg
      if (Pitch[t] < -180) {
        Pitch[t] <- Pitch[t] + 360
      } else if (Pitch[t] > 180) {
        Pitch[t] <- Pitch[t] - 360
      }
      
      # Bout initiation mechanism
      if (Prior_Short == 0) {
        if (t - Bout_Index[length(Bout_Index)] <= t_offset) {
          P_bout <- 0
        } else if (t - Bout_Index[length(Bout_Index)] < tEnd) {
          P_bout <- (basalboutrate / samplerate) * (t - Bout_Index[length(Bout_Index)] - t_offset) * (1 / tEnd)
        } else {
          P_bout <- (basalboutrate / samplerate)
        }
      } else {
        # Calculate a posture-variant P_bout
        if (AngVel[t] > center_angVel) {
          angvel_pbout <- (m_up * (AngVel[t] - center_angVel)) / samplerate
        } else {
          angvel_pbout <- (m_down * (AngVel[t] - center_angVel)) / samplerate
        }
        
        pitch_pbout <- (basalboutrate + pitchsensitivity * (Pitch[t] - pref_posture)^2) / samplerate
        
        if (t - Bout_Index[length(Bout_Index)] <= t_offset) {
          P_bout <- 0
        } else if (t - Bout_Index[length(Bout_Index)] < tEnd) {
          P_bout <- (pitch_pbout + angvel_pbout) * (t - Bout_Index[length(Bout_Index)] - t_offset) * (1 / tEnd)
        } else {
          P_bout <- (pitch_pbout + angvel_pbout)
        }
      }
      
      # Initiate bout if a random number is smaller than P_bout
      if (runif(1) < P_bout) {
        # Calculate net pitch change across bout
        if (Pitch_Correction_Switch == 0) {
          netrot <- rnorm(1, Net_Bout_Rotation_Mean, Net_Bout_Rotation_SD)
        } else {
          if (Pitch[t] < linearportion_pitchchg[2] & Pitch[t] > linearportion_pitchchg[1]) {
            netrot <- rnorm(1, Net_Bout_Rotation_Fit[1] * Pitch[t] + Net_Bout_Rotation_Fit[2], Net_Bout_Rotation_SD)
          } else {
            if (Pitch[t] > linearportion_pitchchg[2]) {
              netrot <- rnorm(1, Net_Bout_Rotation_Fit[1] * linearportion_pitchchg[2] + Net_Bout_Rotation_Fit[2], Net_Bout_Rotation_SD * (1 - NetBoutRsq^2))
            } else {
              netrot <- rnorm(1, Net_Bout_Rotation_Fit[1] * linearportion_pitchchg[1] + Net_Bout_Rotation_Fit[2], Net_Bout_Rotation_SD * (1 - NetBoutRsq^2))
            }
          }
        }
        
        if (abs(netrot) < abs_max_pitchchg) {
          Net_Bout_Rotation <- c(Net_Bout_Rotation, netrot)
        } else {
          if (netrot > abs_max_pitchchg) {
            Net_Bout_Rotation <- c(Net_Bout_Rotation, abs_max_pitchchg)
          } else {
            Net_Bout_Rotation <- c(Net_Bout_Rotation, -abs_max_pitchchg)
          }
        }
        
        # Calculate net angular velocity change across bout
        if (AngVel_Correction_Switch == 0) {
          Net_Bout_AngAcc <- c(Net_Bout_AngAcc, rnorm(1, Net_Bout_AngAcc_Mean, Net_Bout_AngAcc_SD))
        } else {
          Net_Bout_AngAcc <- c(Net_Bout_AngAcc, rnorm(1, AngAcc_Fit[1] * AngVel[t] + AngAcc_Fit[2], SliceAngAcc_SD * (1 - AngAcc_Rsquared^2)))
        }
        
        # Append bout initiation time
        Bout_Index <- c(Bout_Index, t)
        # Append pre-bout posture for diagnostics
        Pre_Bout_Pitch <- c(Pre_Bout_Pitch, Pitch[t])
        Pre_Bout_AngVel <- c(Pre_Bout_AngVel, AngVel[t])
        
        # Advance by bout duration
        t <- t + SwimBout_Duration
        # Apply net bout rotation and net bout angular acceleration across bout
        Pitch[t] <- Pitch[t - SwimBout_Duration] + Net_Bout_Rotation[length(Net_Bout_Rotation)]
        AngVel[t] <- AngVel[t - SwimBout_Duration] + Net_Bout_AngAcc[length(Net_Bout_AngAcc)]
        
        # interpolate pitch during bout (skipped time-steps)
        Pitch[(t - SwimBout_Duration + 1):(t - 1)] <- seq(Pitch[t - SwimBout_Duration], Pitch[t], length.out = SwimBout_Duration - 1)
        AngVel[(t - SwimBout_Duration + 1):(t - 1)] <- seq(AngVel[t - SwimBout_Duration], AngVel[t], length.out = SwimBout_Duration - 1)
      }
    }
    
    # Calculate IEIs from bout initiation times
    modelIEIs <- diff(Bout_Index) / samplerate
    
    # Crop pitch and angular velocity if bout advanced past Model_Duration (
    if (length(Pitch) > Model_Duration * samplerate) {
      Pitch <- Pitch[1:(Model_Duration * samplerate)]
    }
    if (length(AngVel) > Model_Duration * samplerate) {
      AngVel <- AngVel[1:(Model_Duration * samplerate)]
    }
    
    # Calculate IEI histogram
    edges <- seq(0, 20, length.out = num_Bins + 1)
    IEI_dist <- hist(modelIEIs, breaks = edges, plot = FALSE)$counts
    
    # Make probability distribution
    IEI_dist <- IEI_dist / sum(IEI_dist)
    
    # Store IEI probability distribution across simulations
    if (model_Iteration == 1) {
      All_Counts_IEI <- matrix(IEI_dist, nrow = num_Iterations, ncol = length(IEI_dist), byrow = TRUE)
    } else {
      All_Counts_IEI[model_Iteration, ] <- IEI_dist
    }
  }
  
  # Average IEI probability distribution across simulations
  if (num_Iterations > 1) {
    IEI_dist <- colMeans(All_Counts_IEI, na.rm = TRUE)
  }
  
  return(IEI_dist)
  }