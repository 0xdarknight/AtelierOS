(supplier EcoTextile
  (location Vietnam)
  (moq-standard 500)
  (moq-negotiable 250)
  (batch-ordering-available true)
  (lead-time 28)
  (certifications GOTS OEKO-TEX WRAP)
  (cost-per-unit 42)
  (quality-rating 4.7)
  (specialization activewear sustainable-basics)
  (materials organic-cotton recycled-polyester tencel)
  (payment-terms 30-percent-deposit 70-percent-before-ship))

(supplier QuickFactory
  (location China-Guangzhou)
  (moq-standard 1000)
  (moq-negotiable 800)
  (batch-ordering-available false)
  (lead-time 21)
  (certifications ISO9001 OEKO-TEX)
  (cost-per-unit 38)
  (quality-rating 4.2)
  (specialization streetwear basics)
  (materials virgin-polyester cotton blends)
  (payment-terms 50-percent-deposit 50-percent-before-ship))

(supplier PremiumKnits
  (location Portugal)
  (moq-standard 300)
  (moq-negotiable 200)
  (batch-ordering-available true)
  (lead-time 35)
  (certifications GOTS RWS FSC OEKO-TEX)
  (cost-per-unit 56)
  (quality-rating 4.9)
  (specialization premium-activewear technical-wear)
  (materials merino-wool organic-cotton recycled-polyester)
  (payment-terms 40-percent-deposit 60-percent-before-ship))

(supplier BudgetProduction
  (location Bangladesh)
  (moq-standard 2000)
  (moq-negotiable 1500)
  (batch-ordering-available false)
  (lead-time 35)
  (certifications WRAP OEKO-TEX)
  (cost-per-unit 28)
  (quality-rating 3.8)
  (specialization basics fast-fashion)
  (materials cotton polyester blends)
  (payment-terms 50-percent-deposit 50-percent-before-ship))

(supplier LocalMakers
  (location USA-California)
  (moq-standard 100)
  (moq-negotiable 50)
  (batch-ordering-available true)
  (lead-time 14)
  (certifications GOTS OEKO-TEX)
  (cost-per-unit 75)
  (quality-rating 4.8)
  (specialization custom-small-batch sustainable)
  (materials organic-cotton recycled-polyester tencel)
  (payment-terms 50-percent-deposit 50-percent-on-delivery))

(supplier TechApparel
  (location Taiwan)
  (moq-standard 500)
  (moq-negotiable 400)
  (batch-ordering-available true)
  (lead-time 32)
  (certifications ISO9001 OEKO-TEX bluesign)
  (cost-per-unit 48)
  (quality-rating 4.6)
  (specialization technical-activewear outdoor-gear)
  (materials recycled-polyester nylon technical-fabrics)
  (payment-terms 40-percent-deposit 60-percent-before-ship))

(= (find-low-moq-suppliers $category $max-units)
   (match &self
     (supplier $name
       (moq-negotiable $moq)
       (batch-ordering-available $batch)
       (specialization $specs)
       (cost-per-unit $cost))
     (if (and (<= $moq $max-units) (eq $batch true))
         (tuple $name $moq $cost))))

(= (optimal-supplier $budget $min-moq $max-lead-time $required-certs $quality-min)
   (match &self
     (supplier $name
       (moq-negotiable $moq)
       (lead-time $time)
       (certifications $certs)
       (cost-per-unit $cost)
       (quality-rating $rating))
     (if (and (<= $moq $min-moq)
              (<= $time $max-lead-time)
              (>= $rating $quality-min))
         (tuple $name $cost $time $rating))))

(= (supplier-by-material $material-name $max-moq)
   (match &self
     (supplier $name
       (materials $materials)
       (moq-negotiable $moq)
       (cost-per-unit $cost))
     (if (<= $moq $max-moq)
         (tuple $name $cost))))

(= (calculate-total-supplier-cost $supplier-name $units)
   (match &self
     (supplier $supplier-name
       (cost-per-unit $cpu)
       (moq-negotiable $moq))
     (if (>= $units $moq)
         (* $cpu $units)
         (* $cpu $moq))))

(shipping-route Vietnam USA-WestCoast (duration-days 14) (cost-per-unit 3.50) (method sea-freight))
(shipping-route China-Guangzhou USA-WestCoast (duration-days 16) (cost-per-unit 2.80) (method sea-freight))
(shipping-route Portugal USA-WestCoast (duration-days 21) (cost-per-unit 8.50) (method sea-freight))
(shipping-route Bangladesh USA-WestCoast (duration-days 18) (cost-per-unit 2.50) (method sea-freight))
(shipping-route USA-California USA-WestCoast (duration-days 2) (cost-per-unit 1.20) (method ground))
(shipping-route Taiwan USA-WestCoast (duration-days 15) (cost-per-unit 3.20) (method sea-freight))

(= (calculate-shipping-cost $supplier $units)
   (match &self
     (and (supplier $supplier (location $loc))
          (shipping-route $loc USA-WestCoast (cost-per-unit $cpu)))
     (* $cpu $units)))
