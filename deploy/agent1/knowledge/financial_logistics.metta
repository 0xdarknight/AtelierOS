(duty-rate-usa woven-apparel
  (hts-code 6203-6211)
  (rate 16.5-percent)
  (calculation-base fob-value)
  (exemptions-gsp bangladesh india)
  (de-minimis-threshold 800-usd))

(duty-rate-usa knit-apparel
  (hts-code 6101-6117)
  (rate 16.0-percent)
  (calculation-base fob-value)
  (exemptions-gsp certain-developing-countries))

(duty-rate-usa synthetic-apparel
  (hts-code 6201-6217)
  (rate 28.2-32.0-percent)
  (calculation-base fob-value)
  (notes higher-for-non-cotton-synthetic))

(shipping-cost sea-freight
  (origin china-guangzhou)
  (destination usa-los-angeles)
  (transit-days 14-16)
  (cost-per-cbm 80-120-usd)
  (cost-per-unit-estimate 2.80-3.50-usd)
  (minimum-charge 200-usd)
  (fuel-surcharge 15-percent-variable)
  (peak-season-surcharge oct-dec 25-percent-extra))

(shipping-cost sea-freight
  (origin vietnam-ho-chi-minh)
  (destination usa-los-angeles)
  (transit-days 16-18)
  (cost-per-cbm 90-130-usd)
  (cost-per-unit-estimate 3.00-3.80-usd))

(shipping-cost sea-freight
  (origin india-mumbai)
  (destination usa-new-york)
  (transit-days 18-21)
  (cost-per-cbm 100-140-usd)
  (cost-per-unit-estimate 3.20-4.00-usd))

(shipping-cost sea-freight
  (origin bangladesh-chittagong)
  (destination usa-new-york)
  (transit-days 21-24)
  (cost-per-cbm 95-135-usd)
  (cost-per-unit-estimate 3.00-3.70-usd))

(shipping-cost air-freight
  (origin china-guangzhou)
  (destination usa-los-angeles)
  (transit-days 3-5)
  (cost-per-kg 4.50-6.50-usd)
  (cost-per-unit-estimate 9.00-13.00-usd)
  (minimum-charge 500-usd)
  (use-case rush-orders sample-shipments))

(customs-clearance usa-standard
  (broker-fee-per-shipment 75-150-usd)
  (entry-filing-fee 50-75-usd)
  (bond-cost 50-150-usd-annual)
  (examination-fee-if-selected 150-300-usd)
  (clearance-time-days 2-5)
  (documents-required commercial-invoice packing-list bill-of-lading))

(warehouse-costs usa-3pl-standard
  (receiving-fee-per-unit 0.50-0.75-usd)
  (storage-per-pallet-per-month 15-25-usd)
  (pick-pack-fee-per-unit 2.50-3.50-usd)
  (kitting-fee-per-unit 1.00-1.50-usd)
  (return-processing-fee 3.00-4.50-usd)
  (monthly-minimum 200-500-usd))

(warehouse-costs usa-3pl-premium
  (receiving-fee-per-unit 0.60-1.00-usd)
  (storage-per-pallet-per-month 20-35-usd)
  (pick-pack-fee-per-unit 3.00-4.50-usd)
  (value-added-services photography labeling-custom)
  (monthly-minimum 500-1000-usd)
  (providers shipbob shipmonk flexport))

(quality-inspection-cost third-party
  (provider qima inspectorio bureau-veritas)
  (pre-shipment-inspection 200-350-usd)
  (during-production-inspection 250-400-usd)
  (full-audit-factory 800-1500-usd)
  (lab-testing-fabric 150-300-usd-per-test)
  (turnaround-days 1-2-business-days))

(= (calculate-landed-cost $fob $origin $units $product-category)
   (match &self
     (and (shipping-cost sea-freight (origin $origin) (cost-per-unit-estimate $freight-min $freight-max))
          (duty-rate-usa $product-category (rate $duty-pct))
          (customs-clearance usa-standard (broker-fee-per-shipment $broker))
          (warehouse-costs usa-3pl-standard (receiving-fee-per-unit $receiving-min $receiving-max)))
     (let* ((freight-per-unit (/ (+ $freight-min $freight-max) 2))
            (duty-amount (* $fob (/ $duty-pct 100)))
            (broker-per-unit (/ $broker $units))
            (receiving-per-unit (/ (+ $receiving-min $receiving-max) 2))
            (inspection-per-unit 0.40)
            (landed (+ $fob freight-per-unit duty-amount broker-per-unit receiving-per-unit inspection-per-unit)))
       landed)))

(= (calculate-total-landed-cost-batch $fob $origin $units $product-category)
   (let ((per-unit-landed (calculate-landed-cost $fob $origin $units $product-category)))
     (* per-unit-landed $units)))

(cash-flow-scenario startup-small-batch
  (initial-capital 12000-usd)
  (production-units 250)
  (timeline
    (month-minus-3 (outflow sample-development 1500-usd))
    (month-minus-2 (outflow deposit-40-percent 9400-usd))
    (month-minus-1 (outflow balance-payment 14100-usd) (outflow marketing-launch 3000-usd))
    (month-0 (outflow inventory-receiving 500-usd))
    (month-1 (inflow sales 8500-usd) (outflow ops-fulfillment 1200-usd))
    (month-2 (inflow sales 12000-usd) (outflow ops-fulfillment 1500-usd))
    (month-3 (inflow sales 15000-usd) (outflow reorder-deposit 8000-usd) (outflow ops 1500-usd)))
  (cumulative-cash
    (month-minus-3 10500-usd)
    (month-minus-2 1100-usd)
    (month-minus-1 negative-16000-usd)
    (month-0 negative-16500-usd)
    (month-1 negative-9200-usd)
    (month-2 negative-700-usd)
    (month-3 4800-usd))
  (breakeven-month month-3)
  (capital-required-minimum 18000-usd-to-avoid-negative)
  (risk-factors sample-costs-underestimated marketing-overspend slower-sales))

(cash-flow-scenario startup-standard
  (initial-capital 25000-usd)
  (production-units 500)
  (timeline
    (month-minus-4 (outflow samples 2000-usd))
    (month-minus-2 (outflow deposit-40-percent 18800-usd))
    (month-minus-1 (outflow balance-payment 28200-usd) (outflow marketing 5000-usd))
    (month-0 (outflow receiving-customs 1000-usd))
    (month-1 (inflow sales 15000-usd) (outflow ops 2000-usd))
    (month-2 (inflow sales 22000-usd) (outflow ops 2500-usd))
    (month-3 (inflow sales 28000-usd) (outflow ops 3000-usd))
    (month-4 (inflow sales 32000-usd) (outflow reorder 20000-usd) (outflow ops 3500-usd)))
  (cumulative-cash
    (month-minus-4 23000-usd)
    (month-minus-2 4200-usd)
    (month-minus-1 negative-29000-usd)
    (month-0 negative-30000-usd)
    (month-1 negative-17000-usd)
    (month-2 2500-usd)
    (month-3 27500-usd)
    (month-4 36000-usd))
  (breakeven-month month-2)
  (capital-required-minimum 32000-usd-to-stay-positive))

(pricing-strategy cost-plus-standard
  (cogs-to-wholesale-multiplier 2.2-2.5)
  (wholesale-to-retail-multiplier 2.0-2.2)
  (total-cogs-to-retail 4.4-5.5)
  (gross-margin-target 55-65-percent)
  (use-case wholesale-and-dtc-hybrid))

(pricing-strategy dtc-only
  (landed-cost-to-retail 2.5-3.0)
  (gross-margin-target 60-67-percent)
  (includes-marketing-in-cogs 15-20-percent-of-retail)
  (use-case shopify-only-brands))

(pricing-strategy premium-positioning
  (landed-cost-to-retail 3.5-4.5)
  (gross-margin-target 70-78-percent)
  (justification brand-premium sustainable-story quality)
  (use-case luxury-sustainable-designer))

(= (calculate-recommended-retail-price $landed-cost $positioning-strategy $market-comp-avg)
   (match &self
     (pricing-strategy $positioning-strategy (landed-cost-to-retail $multiplier-min $multiplier-max)
                                             (gross-margin-target $margin-min $margin-max))
     (let* ((price-from-cost (* $landed-cost (/ (+ $multiplier-min $multiplier-max) 2)))
            (price-adjusted-market (if (> price-from-cost (* $market-comp-avg 1.15))
                                       (* $market-comp-avg 1.10)
                                       price-from-cost))
            (price-rounded (round-to-9 $price-adjusted-market)))
       price-rounded)))

(= (round-to-9 $price)
   (let* ((rounded-down (* (floor (/ $price 10)) 10))
          (final-price (- (+ rounded-down 10) 1)))
     final-price))

(inventory-planning initial-order
  (method size-curve-distribution)
  (total-units 500)
  (size-curve-activewear
    (xs 4-percent 20-units)
    (s 18-percent 90-units)
    (m 32-percent 160-units)
    (l 28-percent 140-units)
    (xl 14-percent 70-units)
    (xxl 4-percent 20-units))
  (color-distribution
    (neutral-1-black 40-percent)
    (neutral-2-white-grey 35-percent)
    (color-accent 25-percent))
  (weeks-of-inventory-target 8-12-weeks)
  (reorder-trigger 30-percent-remaining))

(inventory-planning reorder-calculation
  (method demand-based-forecast)
  (inputs
    (avg-weekly-sales-by-sku historical-4-weeks)
    (lead-time-weeks 6-weeks-production-plus-shipping)
    (safety-stock-weeks 2-weeks))
  (formula reorder-qty equals
    (lead-time-demand plus safety-stock minus current-stock))
  (example
    (sku hoodie-black-m)
    (avg-weekly-sales 8-units)
    (lead-time 6-weeks)
    (lead-time-demand 48-units)
    (safety-stock 16-units)
    (current-stock 12-units)
    (reorder-quantity 52-units)))

(= (calculate-reorder-quantity $sku $avg-weekly-sales $lead-time-weeks $current-stock)
   (let* ((safety-stock-weeks 2)
          (total-weeks (+ $lead-time-weeks safety-stock-weeks))
          (total-demand (* $avg-weekly-sales total-weeks))
          (reorder-qty (- total-demand $current-stock)))
     (if (> $reorder-qty 0) $reorder-qty 0)))

(payment-terms-standard manufacturer
  (deposit 30-40-percent-upfront)
  (balance 60-70-percent-before-shipment)
  (net-terms rare-for-new-brands)
  (letter-of-credit accepted-adds-cost-1-2-percent)
  (early-payment-discount 2-percent-for-full-prepayment)
  (milestone-payments available-for-large-orders-50k-plus))

(payment-terms-negotiated experienced-brand
  (deposit 30-percent)
  (balance-30-days-after-bl 70-percent)
  (requirements 3-plus-orders-history payment-track-record)
  (credit-check required)
  (personal-guarantee may-be-required))

(season-planning fashion-calendar
  (spring-summer
    (design-development oct-dec)
    (sampling-approval jan-feb)
    (production feb-mar)
    (delivery apr-may)
    (selling-season apr-aug))
  (fall-winter
    (design-development apr-jun)
    (sampling-approval jul-aug)
    (production aug-sep)
    (delivery oct-nov)
    (selling-season oct-feb)))

(risk-factor chinese-new-year
  (timing late-jan-to-mid-feb-variable)
  (impact factory-closure-14-21-days)
  (mitigation place-orders-60-days-before plan-for-delays)
  (affected-regions china vietnam taiwan))

(risk-factor monsoon-season
  (timing jun-sep)
  (impact shipping-delays fabric-delays-india-bangladesh)
  (affected-regions south-asia bangladesh india)
  (mitigation add-1-week-buffer-to-timelines))

(risk-factor port-congestion
  (frequency sporadic-seasonal)
  (impact 1-2-weeks-delay-customs-clearance)
  (affected-ports los-angeles long-beach new-york)
  (mitigation book-freight-early-plan-air-backup))
