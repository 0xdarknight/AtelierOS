(brand-category sustainable-fashion (target-demographic millennials gen-z) (growth-rate 23))
(brand-category activewear (target-demographic fitness-enthusiasts urban-professionals) (growth-rate 18))
(brand-category streetwear (target-demographic gen-z millennials) (growth-rate 15))
(brand-category luxury (target-demographic high-income) (growth-rate 8))

(market-trend 2025 circular-economy (growth-rate 23) (market-size 10billion))
(market-trend 2025 tech-integrated-apparel (growth-rate 28) (market-size 5billion))
(market-trend 2025 gender-neutral-fashion (growth-rate 31) (market-size 3billion))
(market-trend 2025 local-manufacturing (growth-rate 20) (market-size 8billion))

(competitor-analysis activewear Lululemon (avg-price 98) (market-saturation high) (positioning premium-yoga))
(competitor-analysis activewear Nike (avg-price 75) (market-saturation high) (positioning athletic-performance))
(competitor-analysis activewear Outdoor-Voices (avg-price 65) (market-saturation medium) (positioning casual-active))
(competitor-analysis activewear Girlfriend-Collective (avg-price 68) (market-saturation low) (positioning sustainable-inclusive))

(competitor-analysis streetwear Supreme (avg-price 150) (market-saturation high) (positioning hype-limited))
(competitor-analysis streetwear Stussy (avg-price 85) (market-saturation medium) (positioning classic-surf))
(competitor-analysis streetwear Carhartt-WIP (avg-price 95) (market-saturation medium) (positioning workwear-inspired))

(design-style minimalist (trend-score 92) (compatible-with activewear streetwear casual))
(design-style maximalist (trend-score 78) (compatible-with streetwear luxury))
(design-style technical (trend-score 88) (compatible-with activewear outdoor))
(design-style vintage (trend-score 85) (compatible-with streetwear casual))

(material organic-cotton
  (sustainability-score 85)
  (cost-per-meter 8)
  (lead-time 3)
  (properties breathable soft hypoallergenic)
  (certifications GOTS OEKO-TEX))

(material recycled-polyester
  (sustainability-score 82)
  (cost-per-meter 6)
  (lead-time 2)
  (properties moisture-wicking durable quick-dry)
  (certifications GRS OEKO-TEX))

(material virgin-polyester
  (sustainability-score 35)
  (cost-per-meter 4)
  (lead-time 2)
  (properties moisture-wicking durable stretchy)
  (certifications OEKO-TEX))

(material merino-wool
  (sustainability-score 78)
  (cost-per-meter 18)
  (lead-time 4)
  (properties temperature-regulation odor-resistant soft)
  (certifications ZQ RWS))

(material tencel
  (sustainability-score 90)
  (cost-per-meter 12)
  (lead-time 3)
  (properties soft breathable biodegradable)
  (certifications FSC OEKO-TEX))

(color-palette earth-tones
  (colors beige olive cream terracotta)
  (season fall-winter)
  (trend-score 89))

(color-palette neutrals
  (colors black white grey navy)
  (season all-season)
  (trend-score 95))

(color-palette pastels
  (colors lavender mint peach sky-blue)
  (season spring-summer)
  (trend-score 82))

(color-palette bold
  (colors red cobalt emerald yellow)
  (season spring-summer)
  (trend-score 76))

(= (find-market-gap $category)
   (match &self
     (and (brand-category $category $demo)
          (market-trend 2025 $trend $rate)
          (competitor-analysis $category $competitor $price $saturation))
     (if (and (> $rate 15) (eq $saturation low))
         (tuple $trend $saturation))))

(= (best-material $style $budget $sustainability-min)
   (match &self
     (and (material $name (sustainability-score $score) (cost-per-meter $cost))
          (design-style $style (compatible-with $categories)))
     (if (and (< $cost $budget) (> $score $sustainability-min))
         (tuple $name $cost $score))))

(= (optimal-price-point $category $positioning)
   (match &self
     (competitor-analysis $category $competitor $price $saturation)
     (if (eq $positioning premium)
         (* $price 1.15)
         (* $price 0.95))))

(target-audience urban-cyclists
  (age-range 25 40)
  (income-range 60000 120000)
  (values sustainability convenience style)
  (pain-points commute-comfort weather-protection storage))

(target-audience fitness-enthusiasts
  (age-range 20 45)
  (income-range 40000 100000)
  (values performance recovery health)
  (pain-points quality durability comfort))

(target-audience eco-conscious-consumers
  (age-range 22 38)
  (income-range 50000 110000)
  (values sustainability ethics transparency)
  (pain-points greenwashing certifications impact))
