### Library
library(ggplot2)
library(ggpmisc)
library(cowplot)

#############
### Input ###
#############
rm(list = ls())
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
data_day = read.csv("rot_l_decel_2D_day.csv", header = T)  # Day
data_night = read.csv("rot_l_decel_2D_night.csv", header = T)  # Night

### Data frame for plotting
selection = c("pitch_initial", "rot_l_decel", "cond1")
plot_day = data_day[, selection]
plot_night = data_night[, selection]

### Switch to factor
plot_day$cond1 <- as.factor(plot_day$cond1)
plot_night$cond1 <- as.factor(plot_night$cond1)

### Remove big dataframe
rm(data_day, data_night)

### Separate by conditions
day_dd <- plot_day[plot_day$cond1 == "dd",]
day_ll <- plot_day[plot_day$cond1 == "ll",]
day_ld <- plot_day[plot_day$cond1 == "ld",]
night_dd <- plot_night[plot_night$cond1 == "dd",]
night_ll <- plot_night[plot_night$cond1 == "ll",]
night_ld <- plot_night[plot_night$cond1 == "ld",]

#########################
### Sigmoid functions ###
#########################
# Fit model with night_ll
y = night_ll$pitch_initial
x = night_ll$rot_l_decel

fit2 <- nls(
  y ~ (Asym / (1 + exp((
    xmid - x
  ) / scal))) + c,
  start = list(
    Asym = 20,
    xmid = -2,
    scal = -3,
    c = -10
  ),
  data = data.frame(x, y),
  control = nls.control(printEval = T)
)

summary(fit2)  

### Plot result
x_predict_fit2 = seq(-15, 20, length.out = length(night_ll$pitch_initial))
y_predict_fit2 = predict(fit2, newdata = data.frame(x = x_predict_fit2))

# Horizontal
# Asymptote = [-7, 37],fish's tolerence limit, when fish achieve heads-down or heads-up of this limit, strong rotation will be triggered
# xmid = -0.15, inflection point has the lowest slope, which is fish's optimal pitch, and fish wants no rotation
# scal = -1.5, larger "k" steeper curve, but here in denominator, smaller "scal" steeper curve, scale parameter on x-axis
# smaller "scal" (absolute value) = gentler in horizontal plot = steeper in vertical plot = larger righting
ggplot(night_ll, aes(rot_l_decel, pitch_initial, col = "red")) +
  geom_point(alpha = 0.01) +
  geom_line(aes(x = x_predict_fit2, y = y_predict_fit2), col = "blue") +
  annotate("text",
           x = 10,
           y = 50,
           label = "Residual standard error = 8156")

# Vertical
ggplot(night_ll, aes(pitch_initial, rot_l_decel, col = "red")) +
  geom_point(alpha = 0.01) +
  geom_line(aes(x = y_predict_fit2, y = x_predict_fit2), col = "blue") +
  ggtitle("night_ll (Logistic,(A/(1+exp((B-x)/C))) + D)") +
  annotate("text",
           x = 10,
           y = 22,
           label = "RSE = 7763")

############################################
### Use for loop, examine all conditions ###
############################################
### creat empty data frame 
conditions = list(day_dd, night_dd, day_ld, night_ld, night_ll, day_ll)
co <- data.frame()
current_co <- data.frame()

### For loop
for (condition in 1:length(conditions)) {
  ### Fitting model
  y = conditions[[condition]]$pitch_initial
  x = conditions[[condition]]$rot_l_decel
  fit2 <- nls(
    y ~ (Asym / (1 + exp((
      xmid - x
    ) / scal))) + c,
    start = list(
      Asym = 20,
      xmid = -2,
      scal = -3,
      c = -10
    ),
    data = data.frame(x, y),
    control = nls.control(printEval = F)
  )
  
  ### Get coefficient table
  print(summary(fit2))  # print coefficient for each repeat 
  current_co <- coef(fit2)  
  names(current_co) = c("Asym", "xmid", "scal", "c")
  current_co = data.frame(as.list(current_co))  # change from named variable to dataframe
  current_co <- cbind(current_co, condition)  # Add together
  co <- rbind(current_co, co)  # coefficient table
  
  ### Plotting
  # x_predict_fit2 = seq(-15, 20, length.out = length(night_ll$pitch_initial))
  # y_predict_fit2 = predict(fit2, newdata = data.frame(x = x_predict_fit2))
  # 
  # 
  # ggplot(conditions[[condition]], aes(pitch_initial, rot_l_decel, col =
  #                                       "red")) +
  #   geom_point(alpha = 0.01) +
  #   geom_line(aes(x = y_predict_fit2, y = x_predict_fit2), col = "blue") +
  #   ggtitle("night_ll (Logistic,(A/(1+exp((B-x)/C))) + D)") +
  #   annotate("text",
  #            x = 10,
  #            y = 22,
  #            label = "RSE = 7763")
}

###################################################
### Plot coefficients and grouped by conditions ###
###################################################
### Add "Lighting" and "Time" conditions
co <- co[order(co$condition, decreasing = FALSE),]
dataset_names = c("day_dd", "night_dd", "day_ld", "night_ld", "night_ll", "day_ll")
co$condition <- dataset_names
lighting <- c("dd", "dd", "ld", "ld", "ll", "ll")
time <- c("day", "night", "day", "night", "night", "day")
co$lighting <- lighting
co$time <- time
co  # Show coefficient table

### Plot "Asymptote"
Asym_lighting <- ggplot(co, aes(x=condition, y = Asym, group = lighting, col = lighting))+
  geom_point()+
  geom_line()
Asym_time <-ggplot(co, aes(x=condition, y = Asym, group = time, col = time))+
  geom_point()+
  geom_line()

### Plot "Scal"
scal_lighting <- ggplot(co, aes(x=condition, y = scal, group = lighting, col = lighting))+
  geom_point()+
  geom_line()
scal_time <- ggplot(co, aes(x=condition, y = scal, group = time, col = time))+
  geom_point()+
  geom_line()

### Plot "xmid"
xmid_lighting <- ggplot(co, aes(x=condition, y = xmid, group = lighting, col = lighting))+
  geom_point()+
  geom_line()
xmid_time <-ggplot(co, aes(x=condition, y = xmid, group = time, col = time))+
  geom_point()+
  geom_line()

### Plot "c"
c_lighting <- ggplot(co, aes(x=condition, y = c, group = lighting, col = lighting))+
  geom_point()+
  geom_line()
c_time <-ggplot(co, aes(x=condition, y = c, group = time, col = time))+
  geom_point()+
  geom_line()

### Upper & lower limit of the curve 
plot_grid(Asym_lighting, Asym_time,
          c_lighting, c_time, 
          ncol = 2, nrow = 2)

### Inflection point & slop of the curve
plot_grid(xmid_lighting, xmid_time,
          scal_lighting, scal_time, 
          ncol = 2, nrow = 2)
