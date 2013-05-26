# load data
library(ggplot2)
library(reshape)

#########################
## Default parameters
#########################
linePlot <- function(df, xlab, title) {
  # plot susceptible vs resistant
  pd <- position_dodge(0)  # in case error bars or points overlap, they can be dodged by setting to 0.1
  ggplot(data=df,
         aes(x=season, y=mean, colour=population)) +
    geom_errorbar(aes(ymin=mean-sem, ymax=mean+sem), width=.1, position=pd) +
    geom_line(position=pd) +
    # geom_point(position=pd, size=3, shape=21, fill="white") + # 21 is filled circle
    scale_colour_hue(name="Population", # Legend label, use darker colors
                     l=40) + # Use darker colors, lightness=40
    ylab("Population size") +
    xlab(xlab) +
    ggtitle(title) +
    theme_bw() +
    theme(legend.justification=c(1,0), legend.position=c(0.95,0.5)) # Position legend in mid right
}

stackedBarPlot <- function(df, xlab, title) {
  # same but as porportional stacked bars
  ggplot(data=df,
         aes(x=season, y=mean, fill=population)) +
    geom_bar(position="fill", stat="identity", width=1) +
    ylab("Proportion of popoulation") +
    xlab(xlab) +
    scale_fill_hue(name="Population", # Legend label, use darker colors
                   l=30) +
    ggtitle(title) +
    theme_bw() +
    theme(legend.justification=c(1,0), legend.position=c(0.95,0.5)) # Position legend in mid right
}

sv <- read.csv('../season_visits.csv')
sv_sr <- data.frame(hour=sv$hour, S=rowSums(sv[,c(3,4)]), R=rowSums(sv[,c(2,5,6)]))
sv_sr_melted <- melt(sv_sr, id="hour")
thousandseasons <- read.csv('../default_500_seasons.csv')
names(thousandseasons) <- names(paramsweep)[1:10]
hundredseasons <- thousandseasons[thousandseasons$season <= 100,]
fortyseasons <- thousandseasons[thousandseasons$season <= 40,]

pdf("default_parameters.pdf", height=6, width=10)
xlab <- "Seasons"
title <- "Size of resistant/susceptible populations over"
linePlot(thousandseasons, xlab, paste(title, "500 seasons"))
stackedBarPlot(thousandseasons, xlab, paste(title, "500 seasons"))
linePlot(hundredseasons, xlab, paste(title, "100 seasons"))
stackedBarPlot(hundredseasons, xlab, paste(title, "100 seasons"))
linePlot(fortyseasons, xlab, paste(title, "40 seasons"))
stackedBarPlot(fortyseasons, xlab, paste(title, "40 seasons"))
ggplot(data=sv_sr_melted,
       aes(x=hour, y=value, colour=variable)) +
  # geom_line() + # uncomment line to plot unsmoothed data
  stat_smooth(method='loess') +
  labs(colour = "Population") +
  ylab("population size") +
  scale_fill_hue(name="Population", # Legend label, use darker colors
                 l=30) +
  ggtitle(paste(title, "a single season")) +
  theme_bw() +
  theme(legend.justification=c(1,0), legend.position=c(0.95,0.5)) # Position legend in mid right
dev.off()


#########################
## Multivariate parameter sweep
#########################
convert.magic <- function(obj,types){
  for (i in 1:length(obj)){
    FUN <- switch(types[i],character = as.character, 
                  numeric = as.numeric, 
                  factor = as.factor)
    obj[,i] <- FUN(obj[,i])
  }
  obj
}

paramsweep <- read.csv('../multi_variate_sweep.csv')
paramsweep <- convert.magic(paramsweep, c('factor', 'factor', 'factor', 'factor', 'factor', 'numeric', 'character', 'numeric', 'numeric', 'numeric'))
paramsweep$grp <- paste(paramsweep[,1],paramsweep[,2],paramsweep[,3],paramsweep[,4],paramsweep[,5])

manyLinesPlot <- function(df, groupby, legendtitle, title) {
  ggplot(data=df,
         aes_string(x='season', y='mean', colour=groupby, group='grp')) +
           geom_line(size=1) +
           scale_colour_brewer(type='qual', palette=2, name=legendtitle) +
           ylab("Population size") +
           xlab("Season") +
           ggtitle(title) +
           theme_bw()
}

paramsweep_sus <- paramsweep[paramsweep$population=="susceptible",]
sub <- subset(paramsweep_sus, (season %% 1)==0)
pdf("multi_variate_plots.pdf", height=6, width=10)
# plot all lines with no colouring
ggplot(data=sub,
       aes_string(x='season', y='mean', group='grp')) +
  geom_line(size=1) +
  ylab("Population size") +
  xlab("Season") +
  ggtitle("Susceptible population size over 500 seasons") +
  theme_bw()
# colour lines by each parameter in turn
title <- "Susceptible population size over 500 seasons by "
manyLinesPlot(sub, "nbees", "Number of\nbees", paste(title, "number of bees"))
manyLinesPlot(sub, "attr_inf", "Infected\nattractiveness", paste(title, "infected attractiveness"))
manyLinesPlot(sub, "inf_penalty", "Infected maternal\npenalty", paste(title, "infected maternal penalty"))
manyLinesPlot(sub, "nb_penalty", "Nonbuzz \npenalty", paste(title, "non-buzz penalty"))
manyLinesPlot(sub, "nb_inf_penalty", "Nonbuzz infected\npenalty", paste(title, "non-buzz infected penalty"))
# boxplots of 500th season susceptible population
sub <- subset(paramsweep_sus, season==500)
ggplot(data=sub,
       aes(x=factor(nbees), y=mean)) +
  geom_boxplot()
ggplot(data=sub,
       aes(x=factor(attr_inf), y=mean)) +
  geom_boxplot()
ggplot(data=sub,
       aes(x=factor(inf_penalty), y=mean)) +
  geom_boxplot()
ggplot(data=sub,
       aes(x=factor(nb_penalty), y=mean)) +
  geom_boxplot()
ggplot(data=sub,
       aes(x=factor(nb_inf_penalty), y=mean)) +
  geom_boxplot()
dev.off()

#########################
## Univariate paramater sweep
#########################

manyLinesPlotCont <- function(df, groupby, legendtitle, title) {
  ggplot(data=df,
         aes_string(x='season', y='mean', colour=groupby, group='grp')) +
    geom_line(size=1) +
    scale_colour_gradient(low = "#009999", high = "#FF7400", name=legendtitle) +
    ylab("Population size") +
    xlab("Season") +
    ggtitle(title) +
    theme_bw()
}

svs <- read.csv('../single_variate_sweep.csv')
svs$grp <- paste(svs[,1],svs[,2],svs[,3],svs[,4],svs[,5])
svs_sus <- svs[svs$population=="susceptible",]
#svs_sus <- subset(svs_sus, season <= 50)
# defaults from model run script:
# 'nbees': 10, 'attr_inf': 0.81, 'inf_penalty': 0.36,
# 'nb_penalty': 0.74, 'nb_inf_penalty': 0.09
pdf("single_variate_plots.pdf", height=6, width=10)
title <- "Susceptible population size over 500 seasons by"
sub <- subset(svs_sus, attr_inf==0.81 & inf_penalty==0.36 & nb_penalty==0.74 & nb_inf_penalty==0.09)
manyLinesPlotCont(sub, "nbees", "Number of\nbees", paste(title, "number of bees"))
sub <- subset(svs_sus, nbees==10 & inf_penalty==0.36 & nb_penalty==0.74 & nb_inf_penalty==0.09)
manyLinesPlotCont(sub, "attr_inf", "Infected\nattractiveness", paste(title, "infected attractiveness"))
sub <- subset(svs_sus, nbees==10 & attr_inf==0.81 & nb_penalty==0.74 & nb_inf_penalty==0.09)
manyLinesPlotCont(sub, "inf_penalty", "Infected maternal\npenalty", paste(title, "infected maternal penalty"))
sub <- subset(svs_sus, nbees==10 & attr_inf==0.81 & inf_penalty==0.36 & nb_inf_penalty==0.09)
manyLinesPlotCont(sub, "nb_penalty", "Nonbuzz\npenalty", paste(title, "non-buzz penalty"))
sub <- subset(svs_sus, nbees==10 & attr_inf==0.81 & inf_penalty==0.36 & nb_penalty==0.74)
manyLinesPlotCont(sub, "nb_inf_penalty", "Nonbuzz infected\npenalty", paste(title, "non-buzz infected penalty"))
dev.off()


equilibria <- subset(sub, mean < 800 & mean > 200)
