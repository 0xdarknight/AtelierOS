(cost-structure product-base
  (cogs variable)
  (shipping-per-unit variable)
  (warehousing-per-unit variable)
  (packaging-per-unit variable)
  (marketplace-fee-percent variable)
  (payment-processing-percent fixed-2.9)
  (marketing-cac variable))

(fixed-costs startup
  (samples 2000)
  (legal-business-setup 500)
  (platform-setup 300)
  (photography-content 1500)
  (website-domain 200)
  (initial-marketing 3000)
  (contingency 1500))

(pricing-strategy cost-plus
  (markup-multiplier 2.5)
  (min-margin-percent 40)
  (competitive-adjustment true))

(pricing-strategy value-based
  (market-research-required true)
  (competitor-comparison true)
  (perceived-value-premium 15-percent))

(pricing-strategy penetration
  (markup-multiplier 2.0)
  (temporary true)
  (duration-months 6))

(= (calculate-profit $retail-price $cogs $shipping $warehouse $pack $marketing)
   (let* ((total-variable (+ $cogs $shipping $warehouse $pack $marketing))
          (marketplace-fee (* $retail-price 0.15))
          (payment-fee (* $retail-price 0.029))
          (total-fees (+ $marketplace-fee $payment-fee))
          (profit (- $retail-price (+ $total-variable $total-fees))))
     profit))

(= (break-even-units $fixed-costs $retail-price $variable-cost-per-unit)
   (/ $fixed-costs (- $retail-price $variable-cost-per-unit)))

(= (calculate-roi $net-profit $total-investment)
   (* (/ $net-profit $total-investment) 100))

(= (optimal-retail-price $cogs $desired-margin-pct)
   (/ $cogs (- 1 (/ $desired-margin-pct 100))))

(product-costs hoodie-standard
  (cogs 42)
  (shipping-per-unit 3.50)
  (warehousing-per-unit 2.00)
  (packaging-per-unit 1.50)
  (marketplace-fee-percent 15)
  (payment-processing-percent 2.9)
  (marketing-cac 15))

(product-costs pants-standard
  (cogs 48)
  (shipping-per-unit 3.80)
  (warehousing-per-unit 2.20)
  (packaging-per-unit 1.80)
  (marketplace-fee-percent 15)
  (payment-processing-percent 2.9)
  (marketing-cac 18))

(product-costs tshirt-basic
  (cogs 18)
  (shipping-per-unit 2.50)
  (warehousing-per-unit 1.20)
  (packaging-per-unit 0.80)
  (marketplace-fee-percent 15)
  (payment-processing-percent 2.9)
  (marketing-cac 12))

(= (total-variable-cost $product)
   (match &self
     (product-costs $product
       (cogs $cogs)
       (shipping-per-unit $ship)
       (warehousing-per-unit $warehouse)
       (packaging-per-unit $pack)
       (marketing-cac $cac))
     (+ $cogs $ship $warehouse $pack $cac)))

(= (calculate-fees $retail-price $marketplace-pct $payment-pct)
   (+ (* $retail-price (/ $marketplace-pct 100))
      (* $retail-price (/ $payment-pct 100))))

(cash-flow-timeline startup-scenario
  (month -2 (outflow 2000) (description samples-and-testing))
  (month -1 (outflow 21000) (description production-payment-50pct))
  (month 0 (outflow 3500) (description launch-marketing-and-inventory))
  (month 1 (inflow 12000) (outflow 1000) (description initial-sales-and-ops))
  (month 2 (inflow 18000) (outflow 1200) (description growing-sales))
  (month 3 (inflow 22000) (outflow 8000) (description peak-sales-reorder)))

(= (net-cash-flow $month)
   (match &self
     (cash-flow-timeline startup-scenario
       (month $month (inflow $in) (outflow $out)))
     (- $in $out)))

(= (cumulative-cash-position $start-month $end-month $initial-capital)
   (if (<= $start-month $end-month)
       (+ (net-cash-flow $start-month)
          (cumulative-cash-position (+ $start-month 1) $end-month $initial-capital))
       $initial-capital))

(inventory-valuation method-fifo)
(inventory-valuation method-weighted-average)

(reorder-trigger sku-level
  (reorder-point 30-percent-remaining)
  (optimal-reorder-qty 50-percent-initial)
  (lead-time-buffer 7-days))

(= (calculate-reorder-quantity $current-stock $avg-daily-sales $lead-time-days)
   (let* ((demand-during-lead (* $avg-daily-sales $lead-time-days))
          (safety-stock (* $avg-daily-sales 7))
          (reorder-qty (+ demand-during-lead safety-stock (- 0 $current-stock))))
     (if (> $reorder-qty 0) $reorder-qty 0)))

(profitability-threshold minimum
  (gross-margin-percent 40)
  (net-margin-percent 15)
  (roi-minimum-percent 25))

(= (is-profitable $gross-margin $net-margin $roi)
   (match &self
     (profitability-threshold minimum
       (gross-margin-percent $min-gross)
       (net-margin-percent $min-net)
       (roi-minimum-percent $min-roi))
     (if (and (>= $gross-margin $min-gross)
              (>= $net-margin $min-net)
              (>= $roi $min-roi))
         true
         false)))

(funding-requirement bootstrap
  (initial-capital-min 10000)
  (initial-capital-recommended 15000)
  (risk-level high))

(funding-requirement angel-seed
  (initial-capital-min 50000)
  (initial-capital-recommended 75000)
  (risk-level medium))

(= (recommend-funding-strategy $available-capital $target-units)
   (if (< $available-capital 15000)
       bootstrap
       angel-seed))
