# Source-qualified adapters. Output gene signatures use the natural-log input scale.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) >= 1)
if (!grepl("^R version 4[.]5[.]1", R.version.string)) stop("Use the R4_51 runtime")
for (pkg in c("jsonlite", "Matrix", "flashier", "ebnm", "gbcd", "ebcd", "DIVAS", "R.utils")) {
  if (!requireNamespace(pkg, quietly = TRUE)) stop("Missing method dependency: ", pkg)
}
if (packageVersion("CVXR") != "1.0.15") stop("Pinned DIVAS requires CVXR 1.0-15")
if (!"SCS" %in% CVXR::installed_solvers()) stop("DIVAS requires the SCS solver")
if (args[[1]] == "preflight") {
  for (pkg in c("gbcd", "ebcd", "DIVAS", "flashier", "ebnm", "CVXR", "scs")) {
    cat(pkg, as.character(packageVersion(pkg)), find.package(pkg), "\n")
  }
  print(sessionInfo())
  if (length(args) > 1) {
    packages <- c("flashier", "ebnm", "CVXR", "scs", "ashr", "irlba", "RSpectra", "Rcpp", "Matrix", "Rmpfr", "R.utils")
    dependencies <- lapply(packages, function(p) list(version = as.character(packageVersion(p)), path = find.package(p)))
    names(dependencies) <- packages
    jsonlite::write_json(dependencies, args[[2]], auto_unbox = TRUE, pretty = TRUE)
  }
  quit(status = 0)
}
stopifnot(length(args) == 3, args[[1]] == "fit")
request <- jsonlite::fromJSON(args[[2]])
out <- args[[3]]
dir.create(out, showWarnings = FALSE, recursive = TRUE)
Y <- as.matrix(Matrix::readMM(request$matrix))
genes <- readLines(request$genes)
cells <- read.delim(request$cells, stringsAsFactors = FALSE, check.names = FALSE)
stopifnot(ncol(Y) == length(genes), nrow(Y) == nrow(cells), !anyDuplicated(genes),
          all(is.finite(Y)), ncol(Y) > 2, nrow(Y) > 2)
dimnames(Y) <- list(cells$cell_id, genes)
set.seed(request$seed)
warnings <- character()
warning_details <- list()
warning_context <- function(w) {
  detail <- list(message = conditionMessage(w), stage = "terminal_or_unknown")
  if (request$method != "gbcd") return(detail)
  frames <- sys.frames()
  functions <- lapply(seq_along(frames), sys.function)
  active <- function(name, package) {
    any(vapply(functions, identical, logical(1), getFromNamespace(name, package)))
  }
  backfit <- which(vapply(functions, identical, logical(1),
                          getFromNamespace("flash_backfit", "flashier")))
  if (length(backfit)) {
    budget <- get("maxiter", envir = frames[[tail(backfit, 1)]], inherits = FALSE)
    detail$maxiter <- budget
    # The pinned upstream fit has two fixed-budget warmups before refinement.
    if (active("fit_gbcd", "gbcd") && identical(as.numeric(budget), 25) &&
        !active("fit_ebmf_to_YY", "gbcd") && !active("fit_ebmf_to_Y", "gbcd")) {
      detail$stage <- "initialization"
    }
  }
  detail
}
started <- proc.time()[[3]]
result <- withCallingHandlers({
  if (request$method == "gbcd") {
    fit <- gbcd::fit_gbcd(Y, Kmax = request$rank,
                          prior = flashier::flash_ebnm(prior_family = "generalized_binary", scale = 0.04),
                          maxiter1 = request$maxiter, maxiter2 = request$maxiter,
                          maxiter3 = request$maxiter,
                          control = list(extrapolate = FALSE), verbose = 0)
    # Upstream reports F$lfc in log2 units, although Y is on the natural-log scale.
    F <- log(2) * fit$F$lfc
    L <- as.matrix(fit$L)
    diagnostics <- list(convergence = "not_exposed_by_upstream_gbcd", final_rank = ncol(F))
    sharing <- rep("posthoc", ncol(F))
  } else if (request$method == "ebcd") {
    # Match the linked HNSCC comparison: gene x cell input, sparse cell memberships.
    # C bypasses upstream X's automatic covariance compression; Z stays in gene space.
    fit <- ebcd::ebcd(C = t(Y), N = ncol(Y), Kmax = request$rank,
                      ebnm_fn = function(x, s) ebnm::ebnm_generalized_binary(x, s, scale = 0.04),
                      maxiter_greedy = request$maxiter, maxiter_backfit = request$maxiter)
    F <- as.matrix(fit$Z)
    L <- as.matrix(fit$EL)
    objective <- fit$vec.obj
    decreasing <- length(objective) > 1 && any(diff(objective) < -1e-5 * (1 + abs(head(objective, -1))))
    diagnostics <- list(final_rank = ncol(F), iterations = length(objective),
                        objective = objective, objective_decreased = decreasing,
                        convergence = if (length(objective) >= request$maxiter) "iteration_limit" else if (decreasing) "objective_decreased" else "upstream_stopping_rule")
    sharing <- rep("posthoc", ncol(F))
  } else if (request$method == "divas") {
    blocknames <- sort(unique(cells$dataset))
    if (length(blocknames) < 2) stop("DIVAS requires at least two study blocks")
    blocks <- lapply(blocknames, function(b) Y[cells$dataset == b, , drop = FALSE])
    names(blocks) <- blocknames
    fit <- DIVAS::DIVASmain(blocks, nsim = request$nsim, seed = request$seed,
                            rowCent = FALSE, colCent = FALSE, iprint = FALSE, ReturnDetail = TRUE)
    # Matched columns are genes: Scores rows therefore correspond to genes, never cells.
    F <- as.matrix(fit$Scores)
    if (is.null(rownames(F)) || !setequal(rownames(F), genes)) stop("DIVAS gene-score identities lost")
    F <- F[genes, , drop = FALSE]
    sharing <- colnames(F)
    L <- Y %*% F %*% solve(crossprod(F) + diag(1e-6, ncol(F)))
    diagnostics <- list(final_rank = ncol(F), convergence = "upstream_subspace_procedure",
                        matched_axis = "genes", nominal_inference_validated = FALSE)
  } else stop("Unknown method: ", request$method)
  stopifnot(nrow(F) == length(genes), nrow(L) == nrow(Y), ncol(F) == ncol(L),
            all(is.finite(F)), all(is.finite(L)))
  list(fit = fit, F = F, L = L, diagnostics = diagnostics, sharing = sharing)
}, warning = function(w) {
  warnings <<- c(warnings, conditionMessage(w))
  warning_details[[length(warning_details) + 1L]] <<- warning_context(w)
})
saveRDS(result$fit, file.path(out, "native_fit.rds"))
write.table(data.frame(gene_id = genes, result$F, check.names = FALSE),
            file.path(out, "signatures.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
write.table(data.frame(cell_id = cells$cell_id, result$L, check.names = FALSE),
            file.path(out, "native_scores.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
jsonlite::write_json(list(method = request$method, requested_rank = request$rank,
                         diagnostics = result$diagnostics, sharing = result$sharing,
                         warnings = warnings, warning_details = warning_details,
                         elapsed_seconds = proc.time()[[3]] - started,
                         input_scale = "natural_log_CP10k", session = capture.output(sessionInfo())),
                     file.path(out, "diagnostics.json"), auto_unbox = TRUE, pretty = TRUE, null = "null")
