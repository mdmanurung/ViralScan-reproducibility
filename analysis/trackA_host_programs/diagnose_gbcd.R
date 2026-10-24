# Replay the pinned adapter while recording the source of each warning.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3, args[[1]] == "fit")
out <- args[[3]]
dir.create(out, recursive = TRUE, showWarnings = FALSE)
if (file.exists(file.path(out, "warning_trace.json"))) stop("Diagnostic replay already recorded")
events <- list()
capture_warning <- function(w) {
  frames <- sys.frames()
  calls <- sys.calls()
  trace <- lapply(seq_along(frames), function(i) {
    frame <- frames[[i]]
    entry <- list(call = paste(deparse(calls[[i]]), collapse = " "))
    for (key in c("maxiter", "maxiter1", "maxiter2", "maxiter3", "tol", "epsilon")) {
      if (exists(key, envir = frame, inherits = FALSE)) {
        value <- get(key, envir = frame, inherits = FALSE)
        if (is.numeric(value) && length(value) <= 3) entry[[key]] <- value
      }
    }
    entry
  })
  events[[length(events) + 1L]] <<- list(message = conditionMessage(w), stack = trace)
  jsonlite::write_json(events, file.path(out, "warning_trace.json"),
                       auto_unbox = TRUE, pretty = TRUE, null = "null")
}
script <- sub("^--file=", "", grep("^--file=", commandArgs(), value = TRUE)[[1]])
adapter <- file.path(dirname(normalizePath(script)), "methods.R")
started <- proc.time()[[3]]
withCallingHandlers(source(adapter, local = new.env(parent = globalenv())),
                    warning = capture_warning)
jsonlite::write_json(list(elapsed_seconds = proc.time()[[3]] - started,
                          warnings_captured = length(events),
                          installed_packages_modified = FALSE),
                     file.path(out, "replay.json"), auto_unbox = TRUE, pretty = TRUE)
