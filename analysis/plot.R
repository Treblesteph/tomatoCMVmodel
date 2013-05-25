  # load data
  sv <- read.csv('../season_visits.csv')
  hundredseasons <- read.csv('../1000_seasons.csv')
  
  # plot hour visits
  library(ggplot2)
  library(reshape)
  sv_melted <- melt(sv, id="hour")
  ggplot(data=sv_melted,
         aes(x=hour, y=value, colour=variable)) +
    # geom_line() + # uncomment line to plot unsmoothed data
    stat_smooth(method='loess') +
    labs(colour = "Population") +
    ylab("population size")
  
  # plot just susceptible vs resistant
  sv_sr <- data.frame(hour=sv$hour, S=rowSums(sv[,c(3,4)]), R=rowSums(sv[,c(2,5,6)]))
  sv_sr_melted <- melt(sv_sr, id="hour")
  ggplot(data=sv_sr_melted,
         aes(x=hour, y=value, colour=variable)) +
    # geom_line() + # uncomment line to plot unsmoothed data
    stat_smooth(method='loess') +
    labs(colour = "Population") +
    ylab("population size")
  
  # plot 100season population count
  hs_melted <- melt(hundredseasons, id="season")
  ggplot(data=hs_melted,
         aes(x=season, y=value, colour=variable)) +
    # geom_line() + # uncomment line to plot unsmoothed data
    stat_smooth(method='loess') +
    labs(colour = "Population") +
    ylab("population size")
  
  # plot just susceptible vs resistant for 110season
  hs_sr <- data.frame(season=hundredseasons$season, S=rowSums(hundredseasons[,c(3,4)]), R=rowSums(hundredseasons[,c(2,5,6)]))
  hs_sr_melted <- melt(hs_sr, id="season")
  ggplot(data=hs_sr_melted,
         aes(x=season, y=value, colour=variable)) +
    # geom_line() + # uncomment line to plot unsmoothed data
    stat_smooth(method='loess') +
    labs(colour = "Population") +
    ylab("population size")