p = 'program-design/hooks/make_report_figures.py'
with open(p, 'r', encoding='utf-8', newline='') as f:
    text = f.read()

# Re-import the old_lines exactly as in the apply script
def cjl(lines):
    return "".join(l + "\r\n" for l in lines)

old_lines = [
    "    js_div_id = div_id",
    "",
    "    script_template = \"\"\"",
    "<script>",
    "(function(){",
    "  var root = document.getElementById('\"\"\" + js_div_id + \"\"\"');",
    "  var X = \"\"\" + js_x_values + \"\"\";",
    "  var PARAMS = [\"\"\" + js_slider_defs + \"\"\" ];",
    "  var CONSTANTS = \"\"\" + js_constants + \"\"\";",
    "  var sliderEls = {}, labelEls = {};",
    "  PARAMS.forEach(function(p){",
    "    var safeName = String(p.name).replace(/[^A-Za-z0-9_-]/g, '_');",
    "    sliderEls[p.name] = document.getElementById('\"\"\" + js_div_id + \"\"\"-slider-' + safeName);",
    "    labelEls[p.name] = document.getElementById('\"\"\" + js_div_id + \"\"\"-val-' + safeName);",
    "  });",
    "  function currentParams(){",
    "    var P = CONSTANTS ? Object.assign({}, CONSTANTS) : {};",
    "    PARAMS.forEach(function(p){ P[p.name] = parseFloat(sliderEls[p.name].value); });",
    "    return P;",
    "  }",
    "  // The agent-authored closed-form body: recompute y for every x in X given",
    "  // the current parameter object P. Scoped sandbox: it can only use X,",
    "  // PARAMS, P, CONSTANTS, Math, JSON — no DOM access, no fetch, no eval,",
    "  // no network.",
    "  var LIVE_FN = function(P){",
    "\"\"\" + js_js_fn_body + \"\"\"",
    "  };",
    "  function refresh(){",
    "    var P = currentParams();",
    "    PARAMS.forEach(function(p){ labelEls[p.name].textContent = parseFloat(sliderEls[p.name].value).toFixed(4); });",
    "    var errEl = document.getElementById('\"\"\" + js_div_id + \"\"\"-err');",
    "    var ynew;",
    "    try {",
    "      ynew = LIVE_FN(P);",
    "      if (!Array.isArray(ynew) || ynew.length !== X.length) {",
    "        throw new Error('js_function_body must return an array of the same length as X (got '",
    "          + (Array.isArray(ynew) ? ynew.length : typeof ynew) + ', expected ' + X.length + ').');",
    "      }",
    "      for (var i = 0; i < ynew.length; i++) {",
    "        if (typeof ynew[i] !== 'number' || !isFinite(ynew[i])) {",
    "          throw new Error('js_function_body returned a non-finite y value (NaN/Inf) at x index ' + i",
    "            + '; check the formula for a division by zero or log(<=0) at the current parameter values.');",
    "        }",
    "      }",
    "    } catch(e) {",
    "      // Do not silently paper over a JS error in the live function body —",
    "      // surface it visibly next to the sliders, matching this project's",
    "      // \"never silently skip a broken piece of output\" rule.",
    "      errEl.textContent = '实时重算出错（js_function_body 本身写错了，或参数越界导致公式出现 NaN/Inf，不是滑块控件坏了）: ' + e.message;",
    "      return;",
    "    }",
    "    errEl.textContent = '';",
    "    Plotly.restyle(root, {y: [ynew]}, [0]);",
    "  }",
    "  PARAMS.forEach(function(p){ sliderEls[p.name].addEventListener('input', refresh); });",
    "  refresh();",
    "})();",
    "</script>",
    "\"\"\"",
    "",
    "    controls_block = (",
    "        '<div class=\"interactive-live-controls\" style=\"padding:8px 16px;font-family:sans-serif;font-size:13px\">'",
    "        '<div style=\"font-weight:600;margin-bottom:6px\">拖动滑块，实时改变曲线'",
    "        '（纯浏览器端对闭式表达式重新求值，不是重新解方程；参数范围与精度由上游声明）</div>'",
    "        + slider_block",
    "        + f'<div id=\"{div_id}-err\" style=\"color:#ff5470;font-size:12px;margin-top:4px\"></div>'",
    "        \"</div>\"",
    "    )",
]

# find which prefix length stops matching
prefix = ""
for k, l in enumerate(old_lines):
    prefix += l + "\r\n"
    if text.count(prefix) != 1:
        print("MISMATCH at line index", k, "line:", repr(l))
        print("prefix so far (last 120 chars):", repr(prefix[-120:]))
        break
else:
    print("ALL LINES MATCH, full old_block count:", text.count(cjl(old_lines)))
