(production-stage sample-design
  (duration-days 5)
  (deliverables mockups tech-packs)
  (next-stage sample-production))

(production-stage sample-production
  (duration-days 10)
  (quality-checks fabric-test construction-test)
  (deliverables physical-sample)
  (next-stage sample-approval))

(production-stage sample-approval
  (duration-days 3)
  (quality-checks fit-test quality-inspection measurements)
  (decision-points approve revise reject)
  (next-stage bulk-production))

(production-stage bulk-production
  (duration-days 28)
  (checkpoints week1-inspection week2-inspection week3-inspection final-qc)
  (quality-checks fabric-inspection construction-check sizing-verification)
  (next-stage quality-control))

(production-stage quality-control
  (duration-days 3)
  (quality-checks final-inspection defect-rate packaging-check)
  (acceptance-criteria defect-rate-below-2-percent sizing-accuracy-95-percent)
  (next-stage ready-to-ship))

(production-stage ready-to-ship
  (duration-days 1)
  (deliverables packed-units shipping-manifest)
  (next-stage in-transit))

(quality-issue loose-stitching
  (severity low)
  (fix-time 1)
  (cost-impact 3-percent)
  (frequency 15-percent))

(quality-issue sizing-incorrect
  (severity high)
  (fix-time 5)
  (cost-impact 10-percent)
  (frequency 8-percent))

(quality-issue fabric-defect
  (severity medium)
  (fix-time 3)
  (cost-impact 15-percent)
  (frequency 5-percent))

(quality-issue color-mismatch
  (severity medium)
  (fix-time 4)
  (cost-impact 8-percent)
  (frequency 12-percent))

(quality-issue construction-error
  (severity high)
  (fix-time 7)
  (cost-impact 12-percent)
  (frequency 6-percent))

(quality-issue packaging-issue
  (severity low)
  (fix-time 1)
  (cost-impact 2-percent)
  (frequency 10-percent))

(= (predict-delay $current-stage $issues)
   (match &self
     (and (production-stage $current-stage (duration-days $standard))
          (quality-issue $issues (fix-time $fix-days)))
     (+ $standard $fix-days)))

(= (calculate-quality-cost-impact $issue-type $base-cost)
   (match &self
     (quality-issue $issue-type (cost-impact $impact-pct))
     (* $base-cost (/ $impact-pct 100))))

(= (total-production-time $start-stage)
   (match &self
     (production-stage $start-stage (duration-days $days) (next-stage $next))
     (if (eq $next ready-to-ship)
         $days
         (+ $days (total-production-time $next)))))

(production-checkpoint week1-inspection
  (checks fabric-quality cutting-accuracy)
  (timing-pct 25)
  (pass-threshold 95-percent))

(production-checkpoint week2-inspection
  (checks assembly-quality stitching-consistency)
  (timing-pct 50)
  (pass-threshold 95-percent))

(production-checkpoint week3-inspection
  (checks sizing-accuracy finishing-quality)
  (timing-pct 75)
  (pass-threshold 95-percent))

(production-checkpoint final-qc
  (checks complete-inspection defect-count packaging)
  (timing-pct 100)
  (pass-threshold 98-percent))

(sample-status design-phase (progress 0) (next-action create-tech-pack))
(sample-status tech-pack-complete (progress 10) (next-action send-to-factory))
(sample-status factory-received (progress 20) (next-action start-production))
(sample-status in-production (progress 40) (next-action await-completion))
(sample-status sample-ready (progress 60) (next-action ship-for-review))
(sample-status in-review (progress 75) (next-action quality-check))
(sample-status approved (progress 100) (next-action start-bulk-production))
(sample-status revision-needed (progress 50) (next-action modify-and-resubmit))

(= (next-milestone $current-status)
   (match &self
     (sample-status $current-status (next-action $action))
     $action))

(revision-reason fit-adjustment (complexity low) (additional-days 3))
(revision-reason color-change (complexity low) (additional-days 2))
(revision-reason construction-change (complexity medium) (additional-days 5))
(revision-reason material-change (complexity high) (additional-days 10))
(revision-reason design-overhaul (complexity high) (additional-days 14))

(= (calculate-revision-delay $reason)
   (match &self
     (revision-reason $reason (additional-days $days))
     $days))
