library(sf)
library(ggplot2)

# --------------------------------------------------
# INPUT 
# --------------------------------------------------
input_gpkg <- input_gpkg <- "C:/Users/user/Documents/GitHub/Roof-shape-classification/3_ASA_index_classification/classified_buildings.gpkg"   # output di asa_classification.py

VARIABLE <- "asp_asa_filtrata"   # variabile confrontata tra le due classi
CLASS_FIELD <- "tipo"          # campo con i valori "flat" / "sloped"

dir.create("output", showWarnings = FALSE)

# --------------------------------------------------
# Carica dati
# --------------------------------------------------
gdf <- st_read(input_gpkg)

flat <- gdf[[VARIABLE]][gdf[[CLASS_FIELD]] == "piano"]
sloped <- gdf[[VARIABLE]][gdf[[CLASS_FIELD]] == "falde"]

# Pulisci NA/Inf
flat <- flat[!is.na(flat) & is.finite(flat)]
sloped <- sloped[!is.na(sloped) & is.finite(sloped)]

# --------------------------------------------------
# Test Mann-Whitney U
# --------------------------------------------------
mw <- wilcox.test(flat, sloped)
n1 <- length(flat)
n2 <- length(sloped)
r <- 1 - (2 * mw$statistic) / (n1 * n2)

cat("\n========== MANN-WHITNEY U TEST ==========\n")
cat("Variabile testata:", VARIABLE, "\n")
cat("N (Flat) =", n1, ", N (Sloped) =", n2, "\n")
cat("Median Flat =", round(median(flat), 4), "\n")
cat("Median Sloped =", round(median(sloped), 4), "\n")
cat("U =", mw$statistic, "\n")
cat("p-value =", format(mw$p.value, digits = 10), "\n")
cat("Effect Size (r) =", round(r, 4), "\n")

# --------------------------------------------------
# Tabella riassuntiva
# --------------------------------------------------
results_table <- data.frame(
  Variable = VARIABLE,
  N_Flat = n1,
  N_Sloped = n2,
  Median_Flat = round(median(flat), 4),
  Median_Sloped = round(median(sloped), 4),
  U_statistic = mw$statistic,
  p_value = format(mw$p.value, digits = 10),
  Effect_Size_r = round(r, 4)
)

cat("\n\nTable: Mann-Whitney U Test Results\n")
print(results_table)

write.csv(results_table, "output/Mann_Whitney_Results.csv", row.names = FALSE)
cat("\nSalvata: output/Mann_Whitney_Results.csv\n")

# --------------------------------------------------
# Versione formattata per il paper
# --------------------------------------------------
cat("\n\n========== FORMATTED FOR PAPER ==========\n\n")
cat("U = ", mw$statistic, ", p = ", format(mw$p.value, digits = 8),
    ", r = ", round(r, 4), "\n\n", sep = "")

# --------------------------------------------------
# Visualizzazione
# --------------------------------------------------
data_all <- data.frame(
  value = c(flat, sloped),
  class = c(rep("Flat", length(flat)), rep("Sloped", length(sloped)))
)

p <- ggplot(data_all, aes(x = value, fill = class)) +
  geom_histogram(bins = 30, alpha = 0.6, position = "identity") +
  scale_fill_manual(values = c("Flat" = "steelblue", "Sloped" = "orange")) +
  ggtitle(paste("Distribuzione di", VARIABLE, ": Flat vs Sloped")) +
  xlab(VARIABLE) +
  ylab("Frequenza") +
  theme_minimal() +
  theme(plot.title = element_text(hjust = 0.5, face = "bold"))

ggsave("output/ASA_flat_vs_sloped.png", p, width = 10, height = 6, dpi = 300)
cat("Salvato: output/ASA_flat_vs_sloped.png\n")
