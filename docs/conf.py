from documenteer.conf.guide import *  # noqa

exclude_patterns = ["_rst_epilog.rst", "**.ipynb"]
nb_execution_mode = "off"

linkcheck_ignore = [
    r"https://github\.com/.*",
    r"https://grafana.slac.stanford.edu/.*",
    r"https://grafana.ls.lsst.org/.*",
    r"https://summit-lsp.lsst.codes/.*",
    r"https://base-lsp.lsst.codes/.*",
    r"https://tucson-teststand.lsst.codes/.*",
    r"https://usdf-rsp-dev.slac.stanford.edu/.*",
    r"https://usdf-rsp-int.slac.stanford.edu/.*",
    r"https://usdf-rsp.slac.stanford.edu/.*",
]

linkcheck_rate_limit_timeout = 300
linkcheck_retries = 1
