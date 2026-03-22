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
# for steering gain:
# x_name_for_fit = 'traj_peak'
# y_name_for_fit = 'pitch_peak'
selection = c("traj_peak", "pitch_peak", "cond1")
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

##################
### Regression ###
##################
### Polynomial ###
##################
# Linear function: y = a +b*x
linear <- ggplot(day_dd, aes(traj_peak, pitch_peak, col = "red"))+
  geom_point(alpha = 0.01)+
  stat_poly_line(color = "blue") +
  stat_poly_eq(use_label(c("adj.R2","eq","F"))) +
  ggtitle("Night time DD (linear)")

# Binomial linear regression: y = a +b*x +c*x^2
binomial <- ggplot(day_dd, aes(traj_peak,pitch_peak, col = "red"))+
  geom_point(alpha = 0.01)+
  stat_poly_line(formula = y ~ poly(x, 2, raw = TRUE), color = "blue") +
  stat_poly_eq(formula = y ~ poly(x, 2, raw = TRUE), use_label(c("adj.R2","eq"))) +
  ggtitle("Night time DD (binomial)")

# Trinomial linear regression: y = a +b*x + c*x^2 + d*x^3
trinomial <- ggplot(day_dd, aes(traj_peak,pitch_peak,  col = "red"))+
  geom_point(alpha = 0.01)+
  stat_poly_line(formula = y ~ poly(x, 3, raw = TRUE), color = "blue") +
  stat_poly_eq(formula = y ~ poly(x, 3, raw = TRUE), use_label(c("adj.R2","eq"))) +
  ggtitle("Night time DD (trinomial)")

plot_grid(linear, binomial, trinomial, ncol = 3, nrow = 1)
linear
#############################
### Two linear regression ###
#############################
# # Split data set at pitch = 10
# night_dd_positve <- night_dd[night_dd$pitch_initial >=10,]
# night_dd_negative <- night_dd[night_dd$pitch_initial <10,]
# 
# # Initial pitch > 10
# positive<- ggplot(night_dd_positve, aes(pitch_initial, rot_l_decel, col = "red"))+
#   geom_point(alpha = 0.01)+
#   stat_poly_line(color = "blue") +
#   stat_poly_eq(use_label(c("adj.R2","eq"))) +
#   ggtitle("Night time DD (initial pitch >= 10)")
# 
# # Initial pitch < 10
# negative<-ggplot(night_dd_negative, aes(pitch_initial, rot_l_decel, col = "red"))+
#   geom_point(alpha = 0.01)+
#   stat_poly_line(color = "blue") +
#   stat_poly_eq(use_label(c("adj.R2","eq"))) +
#   ggtitle("Night time DD negative (initial pitch < 10)")
# 
# plot_grid(negative, positive, 
#           ncol = 2, nrow = 1)

#########################
### Sigmoid functions ###
#########################
# Export x, y 
y = night_dd$pitch_peak 
x = night_dd$traj_peak

# Fit with Self Start logistic model, Asym/(1+exp((xmid-input)/scal))
fit1 <- nls(y ~ SSlogis(x, Asym, xmid, scal), data = data.frame(x, y), 
            control=nls.control(printEval = T))
summary(fit1)

# Plotting based on logistic model
x_predict = seq(-10, 20, length.out = length(night_dd$pitch_peak))
y_predict = predict(fit1, newdata = data.frame(x = x_predict))

# Horizontal plot
# ggplot(night_dd, aes(rot_l_decel, pitch_initial, col ="red"))+
#   geom_point(alpha = 0.01)+
#   geom_line(aes(x=x_predict, y = y_predict), col = "blue")+
#   annotate("text", x = 10, y = 50,  label = "Residual standard error = 9023")

# Vertical plot
logistic_3par <- ggplot(night_dd, aes(pitch_peak, traj_peak, col ="red"))+
  geom_point(alpha = 0.01)+
  geom_line(aes(x=y_predict, y = x_predict), col = "blue")+
  ggtitle("Night time DD (Logistic, A/(1+exp((B-x)/C))")+
  annotate("text", x = 10, y = 22,  label = "Residual standard error = 9023")

###########################
### 4 variable logistic ###
###########################
fit2 <- nls(y ~ (Asym/(1+exp((xmid-x)/scal)))+c,
            start = list(Asym=20, xmid=-2, scal = -3, c = -10),
            data = data.frame(x, y), 
            control=nls.control(printEval = T))

summary(fit2)
x_predict_fit2 = seq(-10, 20, length.out = length(night_dd$pitch_peak))
y_predict_fit2 = predict(fit2, newdata = data.frame(x = x_predict_fit2))

# Horizontal
# ggplot(night_dd, aes(rot_l_decel, pitch_initial, col ="red"))+
#   geom_point(alpha = 0.01)+
#   geom_line(aes(x=x_predict, y = y_predict), col = "blue")+
#   annotate("text", x = 10, y = 50,  label = "Residual standard error = 8156")

# Vertical
logistic_4par <- ggplot(night_dd, aes(pitch_initial, rot_l_decel, col ="red"))+
  geom_point(alpha = 0.01)+
  geom_line(aes(x=y_predict_fit2, y = x_predict_fit2), col = "blue")+
  ggtitle("Night time DD (Logistic,(A/(1+exp((B-x)/C))) + D)")+
  annotate("text", x = 10, y = 22,  label = "RSE = 8156")

######################
### Non-parametric ###
######################

# Locally weighted regression (Loess)
loess<-ggplot(night_dd, aes(pitch_peak,traj_peak, col = "red"))+
  geom_point(alpha = 0.01)+
  stat_smooth(color = "blue")+
  ggtitle("Night time DD (LOESS Regression, no equation)")

plot_grid(logistic_3par, loess, 
          ncol = 2, nrow = 1)

# day_dd.lo <- loess(rot_l_decel ~ pitch_initial, day_dd)
# ss.dist <- sum(scale(day_dd$rot_l_decel, scale=FALSE)^2)
# ss.resid <- sum(resid(day_dd.lo)^2)
# 1-ss.resid/ss.dist




# 
# 
# # Split at pitch = 5
# # Split data into positive & negative pitch initial
# day_dd_positve <- day_dd[day_dd$pitch_initial >=5,]
# day_dd_negative <- day_dd[day_dd$pitch_initial <5,]
# night_dd_positve <- night_dd[night_dd$pitch_initial >=5,]
# night_dd_negative <- night_dd[night_dd$pitch_initial <5,]
# 
# # Run Linear function: y = a +b*x
# positive<- ggplot(night_dd_positve, aes(pitch_initial, rot_l_decel, col = "red"))+
#   geom_point(alpha = 0.01)+
#   stat_smooth(method = "lm")+
#   stat_cor(label.y = max(night_dd_positve$rot_l_decel)*0.90) + 
#   stat_poly_eq(aes(label = after_stat(eq.label)),label.y = max(night_dd_positve$rot_l_decel)*0.95,
#                parse = TRUE)+
#   ggtitle("Night time DD positive pitch")
# 
# negative<-ggplot(night_dd_negative, aes(pitch_initial, rot_l_decel, col = "red"))+
#   geom_point(alpha = 0.01)+
#   stat_smooth(method = "lm")+
#   stat_cor(label.y = max(night_dd_negative$rot_l_decel)*0.90) + 
#   stat_poly_eq(aes(label = after_stat(eq.label)),label.y = max(night_dd_negative$rot_l_decel)*0.95,
#                parse = TRUE)+
#   ggtitle("Night time DD negative pitch")
# 
# plot_grid(negative, positive, 
#           ncol = 2, nrow = 1)
# 
# # Split at pitch = 10
# # Split data into positive & negative pitch initial
# day_dd_positve <- day_dd[day_dd$pitch_initial >=10,]
# day_dd_negative <- day_dd[day_dd$pitch_initial <10,]
# night_dd_positve <- night_dd[night_dd$pitch_initial >=10,]
# night_dd_negative <- night_dd[night_dd$pitch_initial <10,]
# 
# # Run Linear function: y = a +b*x
# positive<- ggplot(night_dd_positve, aes(pitch_initial, rot_l_decel, col = "red"))+
#   geom_point(alpha = 0.01)+
#   stat_smooth(method = "lm")+
#   stat_cor(label.y = max(night_dd_positve$rot_l_decel)*0.90) + 
#   stat_poly_eq(aes(label = after_stat(eq.label)),label.y = max(night_dd_positve$rot_l_decel)*0.95,
#                parse = TRUE)+
#   ggtitle("Night time DD positive pitch")
# 
# negative<-ggplot(night_dd_negative, aes(pitch_initial, rot_l_decel, col = "red"))+
#   geom_point(alpha = 0.01)+
#   stat_smooth(method = "lm")+
#   stat_cor(label.y = max(night_dd_negative$rot_l_decel)*0.90) + 
#   stat_poly_eq(aes(label = after_stat(eq.label)),label.y = max(night_dd_negative$rot_l_decel)*0.95,
#                parse = TRUE)+
#   ggtitle("Night time DD negative pitch")
# 
# plot_grid(negative, positive, 
#           ncol = 2, nrow = 1)
#
# y = rescale(night_dd$pitch_initial, to=c(-1,1)) # Normalize?
# plot(y ~ x)
#
# lines(col = "red", seq(-10, 20, length.out = length(night_dd$pitch_initial)), 
#       predict(fit, newdata = data.frame(x = seq(-10, 20, length.out = length(night_dd$pitch_initial)))))
