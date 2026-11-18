# Methods and interpretation

## Catalogue and coordinates

The pipeline fetches public CelesTrak general perturbations elements in OMM JSON, retains original rows and their epochs, and archives a daily snapshot. Public catalogues are incomplete and are not operator ephemerides. The daily source is the active-object group; it excludes much debris and inactive payloads. A broader local OMM catalogue can be supplied via `--input`. Rows that cannot propagate successfully are omitted from rendered positions and counted during screening.

Python SGP4 uses WGS72; positions are TEME kilometres. Browser satellite.js propagates the same OMM rows at the chosen time. Earth rotation is an approximate GMST visual orientation and not a precision TEME-to-ITRF transform. Coastlines are simplified orientation aids, not geographic data. Client propagation and server screening operate independently; a highlighted encounter marker represents its TCA location, not its current position.

## Close approaches

At each 120-second grid point a KD-tree finds object pairs within a 150 km candidate radius. For each discovered pair, retain the best sampled neighbourhood and minimize SGP4 separation over its adjacent grid interval; check interval endpoints too. Pairs with identical epoch and orbital elements are counted and excluded as shared-element trajectories (for example station modules); this is not a validated physical association classifier. Report up to 100 nearest qualifying pairs below 10 km. Relative speed is a centred one-second finite difference.

There is **no completeness guarantee**: LEO relative motion can cross the discovery radius between samples; multiple encounters can occur between a given pair. Increasing radius and reducing step improves discovery at increased cost. The default 500-object subset is deliberately bounded for free-runner experimentation and is selected by ascending NORAD ID. Coverage must be disclosed in every result; these are not a global top-risk ranking. A production screener needs conservative swept-volume / interval bounds, convergence studies, independent verification, and compute benchmarking. We make no sub-hour full-catalogue claim.

Do not convert miss distances into probabilities without defensible joint position covariance, hard-body radii and an appropriate encounter model. The published field is explicitly null.

## Forecast baseline

Adjacent daily snapshots generate samples. Propagate the older elements to the newer element epoch and subtract that from the newer element's position at its own epoch. Features: intercept, propagation age, mean motion, eccentricity, inclination. Fit a regularized linear regression to three TEME residual components.

Require at least five snapshots and 100 samples. The chronological 70% split boundary is combined with disjoint objects: training IDs modulo 5 are nonzero; test IDs modulo 5 equal zero. Boundary dates belong only to the test interval. Model and uncorrected SGP4 are compared using vector RMSE. The reported held-out 90th-percentile residual is descriptive; it is not a calibrated uncertainty interval for future predictions. No baseline improvement is assumed. The correction is evaluated in research output and is **not applied** to conjunctions or the globe until validated.

Later public element sets are a noisy proxy for truth with correlated fitting errors, not independent measurements. Extend evaluation to multiple horizons, object classes, withheld dates, calibration sets, proper uncertainty scoring and independent precision ephemerides before research claims.

## Manoeuvre candidates

Compare consecutive snapshots at the later epoch, only for element ages 0.1–3 days. Flag residual discontinuities over 5 km. Positive mean-motion changes greater than 0.005 revolutions/day suggest lowering, negative changes suggest raising; others remain unclassified. Changes in drag, fits, epoch age and public data quality produce false positives. This is a heuristic detector and has no reported benchmark precision/recall. Avoidance and deorbit intent cannot be inferred from this alone.

## Displacement estimate

`max(0, target miss − current miss) / lead time` is a straight-line optimistic impulse lower bound. It has no directional solution, nonlinear orbital dynamics, uncertainty, thrust constraints or secondary conjunction screening. It is not a validated dodge planner. No spacecraft command generation is implemented.
