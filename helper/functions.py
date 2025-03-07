"""
Collection of helpful functions for other scripts
"""

import sys
import os
import glob
import array
import numpy as np
import ROOT

from io import StringIO
from wurlitzer import pipes, STDOUT


def check_for_empty_file(path, tree):
    f = ROOT.TFile.Open(path)
    return bool(f.Get(tree))


def get_ntuples(config, sample):
    sample_paths = (
        config["ntuple_path"]
        + "/"
        + config["era"]
        + "/"
        + sample
        + "/"
        + config["channel"]
        + "/*.root"
    )
    print(
        "The following files are loaded for era: {}, channel: {}".format(
            config["era"], config["channel"]
        )
    )
    print("-" * 50)
    print(sample_paths)
    print("-" * 50)

    return sample_paths


def get_samples(config):
    sample_paths = (
        config["file_path"]
        + "/preselection/"
        + config["era"]
        + "/"
        + config["channel"]
        + "/*.root"
    )
    print(
        "The following files are loaded for era: {}, channel: {}".format(
            config["era"], config["channel"]
        )
    )
    print("-" * 50)
    sample_path_list = glob.glob(sample_paths)
    tmp_list = glob.glob(sample_paths)

    for f in tmp_list:
        sample = f.rsplit("/")[-1].rsplit(".")[0]
        if config["use_embedding"] and "_T" in sample:
            sample_path_list.remove(f)
        elif not config["use_embedding"] and sample == "embedding":
            sample_path_list.remove(f)

    for f in sample_path_list:
        print(f)
    print("-" * 50)

    return sample_path_list


def check_output_path(output_path):
    if not os.path.exists(output_path):
        print(
            "Output directory does not exist! Making directory {}".format(output_path)
        )
        print("-" * 50)
        os.makedirs(output_path, exist_ok=True)


def get_output_name(output_path, process, tau_gen_mode, idx=None):
    if tau_gen_mode == "all":
        tau_gen_mode = ""
    else:
        tau_gen_mode = "_" + tau_gen_mode

    if idx is not None:
        return output_path + "/" + process + tau_gen_mode + "_" + str(idx) + ".root"
    else:
        return output_path + "/" + process + tau_gen_mode + ".root"


def check_categories(config):
    for process in config["target_process"]:
        cats = config["target_process"][process]["split_categories"]
        cat_edges = config["target_process"][process]["split_categories_binedges"]
        for cat in cats:
            if len(cats[cat]) != (len(cat_edges[cat]) - 1):
                sys.exit(
                    "Categories and binning for the categories does not match up for {}, {}.".format(
                        process, cat
                    )
                )

    frac_cats = config["process_fractions"]["split_categories"]
    frac_cat_edges = config["process_fractions"]["split_categories_binedges"]
    for cat in frac_cats:
        if len(frac_cats[cat]) != (len(frac_cat_edges[cat]) - 1):
            sys.exit(
                "Categories and binning for the categories does not match up for {} for fractions.".format(
                    cat
                )
            )


def modify_config(config, process, corr_config):
    if "SRlike_cuts" in corr_config:
        for mod in corr_config["SRlike_cuts"]:
            config["target_process"][process]["SRlike_cuts"][mod] = corr_config[
                "SRlike_cuts"
            ][mod]
    if "ARlike_cuts" in corr_config:
        for mod in corr_config["ARlike_cuts"]:
            config["target_process"][process]["ARlike_cuts"][mod] = corr_config[
                "ARlike_cuts"
            ][mod]


def get_split_combinations(categories):
    combinations = list()
    split_vars = list(categories.keys())

    if len(split_vars) == 1:
        for n in categories[split_vars[0]]:
            combinations.append({split_vars[0]: n})
    elif len(split_vars) == 2:
        for n in categories[split_vars[0]]:
            for m in categories[split_vars[1]]:
                combinations.append({split_vars[0]: n, split_vars[1]: m})
    else:
        sys.exit("Category splitting is only defined up to 2 dimensions.")

    return tuple(split_vars), combinations


def QCD_SS_estimate(hists):
    qcd = hists["data"].Clone()

    for sample in hists:
        if sample not in ["data", "data_subtracted", "data_ff", "QCD"]:
            qcd.Add(hists[sample], -1)
    # check for negative bins
    for i in range(qcd.GetNbinsX()):
        if qcd.GetBinContent(i) < 0.0:
            qcd.SetBinContent(i, 0.0)
    return qcd


def calculate_QCD_FF(SRlike, ARlike):
    ratio = SRlike["data_subtracted"].Clone()
    ratio.Divide(ARlike["data_subtracted"])
    ratio_up = SRlike["data_subtracted_up"].Clone()
    ratio_up.Divide(ARlike["data_subtracted_up"])
    ratio_down = SRlike["data_subtracted_down"].Clone()
    ratio_down.Divide(ARlike["data_subtracted_down"])
    return ratio, ratio_up, ratio_down


def calculate_Wjets_FF(SRlike, ARlike):
    ratio = SRlike["data_subtracted"].Clone()
    ratio.Divide(ARlike["data_subtracted"])
    ratio_up = SRlike["data_subtracted_up"].Clone()
    ratio_up.Divide(ARlike["data_subtracted_up"])
    ratio_down = SRlike["data_subtracted_down"].Clone()
    ratio_down.Divide(ARlike["data_subtracted_down"])
    return ratio, ratio_up, ratio_down


def calculate_ttbar_FF(SR, AR, SRlike, ARlike):
    ratio_mc = SR["ttbar_J"].Clone()
    ratio_mc.Divide(AR["ttbar_J"])

    ratio_DR_data = SRlike["data_subtracted"].Clone()
    ratio_DR_data.Divide(ARlike["data_subtracted"])

    ratio_DR_mc = SRlike["ttbar_J"].Clone()
    ratio_DR_mc.Divide(ARlike["ttbar_J"])

    sf = ratio_DR_data.GetMaximum() / ratio_DR_mc.GetMaximum()
    ratio_mc.Scale(sf)

    return ratio_mc


def calc_fraction(hists, target, processes):
    mc = hists[target].Clone()
    for p in processes:
        if p != target:
            mc.Add(hists[p])
    frac = hists[target].Clone()
    frac.Divide(mc)
    return frac


def add_fraction_variations(hists, processes):
    variations = dict()
    variations["nominal"] = dict(hists)

    for p in processes:
        hists_up = dict(hists)
        for hist in hists_up:
            hists_up[hist] = hists_up[hist].Clone()
            if p == hist:
                hists_up[hist].Scale(1.07)
            else:
                hists_up[hist].Scale(0.93)
        variations["frac_{}_up".format(p)] = hists_up

    for p in processes:
        hists_down = dict(hists)
        for hist in hists_down:
            hists_down[hist] = hists_down[hist].Clone()
            if p == hist:
                hists_down[hist].Scale(0.93)
            else:
                hists_down[hist].Scale(1.07)
        variations["frac_{}_down".format(p)] = hists_down

    return variations


def get_yields_from_hists(hists, processes):
    fracs = dict()
    categories = hists.keys()
    for cat in categories:
        v_fracs = dict()
        for var in hists[cat]:
            p_fracs = dict()
            for p in processes:
                h = hists[cat][var][p]
                l = list()
                for b in range(h.GetNbinsX()):
                    l.append(h.GetBinContent(b + 1))
                p_fracs[p] = l
            v_fracs[var] = p_fracs
        fracs[cat] = v_fracs

    return fracs


def fit_function(ff_hist, bin_edges):
    do_mc_subtr_unc = False
    if isinstance(ff_hist, list):
        do_mc_subtr_unc = True
        ff_hist_up = ff_hist[1]
        ff_hist_down = ff_hist[2]
        ff_hist = ff_hist[0]

    nbins = ff_hist.GetNbinsX()

    x = list()
    y = list()
    error_y_up = list()
    error_y_down = list()
    for nbin in range(nbins):
        x.append(ff_hist.GetBinCenter(nbin + 1))
        y.append(ff_hist.GetBinContent(nbin + 1))
        error_y_up.append(ff_hist.GetBinErrorUp(nbin + 1))
        error_y_down.append(ff_hist.GetBinErrorLow(nbin + 1))

    x = array.array("d", x)
    y = array.array("d", y)
    error_y_up = array.array("d", error_y_up)
    error_y_down = array.array("d", error_y_down)

    # Nbins = 448
    # x_arr, resampling_y, resampling_y_up, resampling_y_down = resample(x, y, error_y_up, n=200, bins=Nbins)

    graph = ROOT.TGraphAsymmErrors(nbins, x, y, 0, 0, error_y_down, error_y_up)

    out = StringIO()
    with pipes(stdout=out, stderr=STDOUT):
        fit = graph.Fit("pol1", "SFN")
        if do_mc_subtr_unc:
            fit_up = ff_hist_up.Fit("pol1", "SFN")
            fit_down = ff_hist_down.Fit("pol1", "SFN")
    print(out.getvalue())
    print("-" * 50)

    fit_func = lambda pt: (fit.Parameter(1) * pt + fit.Parameter(0))
    fit_func_slope_up = lambda pt: (
        (fit.Parameter(1) + fit.ParError(1)) * pt + fit.Parameter(0)
    )
    fit_func_slope_down = lambda pt: (
        (fit.Parameter(1) - fit.ParError(1)) * pt + fit.Parameter(0)
    )
    fit_func_norm_up = lambda pt: (
        fit.Parameter(1) * pt + (fit.Parameter(0) + fit.ParError(0))
    )
    fit_func_norm_down = lambda pt: (
        fit.Parameter(1) * pt + (fit.Parameter(0) - fit.ParError(0))
    )
    if do_mc_subtr_unc:
        fit_func_up = lambda pt: (fit_up.Parameter(1) * pt + fit_up.Parameter(0))
        fit_func_down = lambda pt: (fit_down.Parameter(1) * pt + fit_down.Parameter(0))

    cs_expressions = list()
    # best fit
    cs_expressions.append("{}*x+{}".format(fit.Parameter(1), fit.Parameter(0)))
    # slope parameter up/down
    cs_expressions.append(
        "{}*x+{}".format((fit.Parameter(1) + fit.ParError(1)), fit.Parameter(0))
    )
    cs_expressions.append(
        "{}*x+{}".format((fit.Parameter(1) - fit.ParError(1)), fit.Parameter(0))
    )
    # normalization parameter up/down
    cs_expressions.append(
        "{}*x+{}".format(fit.Parameter(1), (fit.Parameter(0) + fit.ParError(0)))
    )
    cs_expressions.append(
        "{}*x+{}".format(fit.Parameter(1), (fit.Parameter(0) - fit.ParError(0)))
    )
    # MC subtraction uncertainty up/down
    if do_mc_subtr_unc:
        cs_expressions.append(
            "{}*x+{}".format(fit_up.Parameter(1), fit_up.Parameter(0))
        )
        cs_expressions.append(
            "{}*x+{}".format(fit_down.Parameter(1), fit_down.Parameter(0))
        )

    y_fit = list()
    y_fit_slope_up = list()
    y_fit_slope_down = list()
    y_fit_norm_up = list()
    y_fit_norm_down = list()
    if do_mc_subtr_unc:
        y_fit_up = list()
        y_fit_down = list()

    x_fit = np.linspace(bin_edges[0], bin_edges[-1], 1000 * nbins)

    for val in x_fit:
        y_fit.append(fit_func(val))
        y_fit_slope_up.append(abs(fit_func_slope_up(val) - fit_func(val)))
        y_fit_slope_down.append(abs(fit_func_slope_down(val) - fit_func(val)))
        y_fit_norm_up.append(abs(fit_func_norm_up(val) - fit_func(val)))
        y_fit_norm_down.append(abs(fit_func_norm_down(val) - fit_func(val)))
        if do_mc_subtr_unc:
            y_fit_up.append(abs(fit_func_up(val) - fit_func(val)))
            y_fit_down.append(abs(fit_func_down(val) - fit_func(val)))

    x_fit = array.array("d", x_fit)
    y_fit = array.array("d", y_fit)
    y_fit_slope_up = array.array("d", y_fit_slope_up)
    y_fit_slope_down = array.array("d", y_fit_slope_down)
    y_fit_norm_up = array.array("d", y_fit_norm_up)
    y_fit_norm_down = array.array("d", y_fit_norm_down)
    if do_mc_subtr_unc:
        y_fit_up = array.array("d", y_fit_up)
        y_fit_down = array.array("d", y_fit_down)

    fit_graph_slope = ROOT.TGraphAsymmErrors(
        len(x_fit), x_fit, y_fit, 0, 0, y_fit_slope_down, y_fit_slope_up
    )
    fit_graph_norm = ROOT.TGraphAsymmErrors(
        len(x_fit), x_fit, y_fit, 0, 0, y_fit_norm_down, y_fit_norm_up
    )
    if do_mc_subtr_unc:
        fit_graph_mc_sub = ROOT.TGraphAsymmErrors(
            len(x_fit), x_fit, y_fit, 0, 0, y_fit_down, y_fit_up
        )
    # resampled_fit_graph = ROOT.TGraphAsymmErrors(
    #     Nbins, x_arr, resampling_y, 0, 0, resampling_y_down, resampling_y_up
    # )
    if do_mc_subtr_unc:
        return {
            "fit_graph_slope": fit_graph_slope,
            "fit_graph_norm": fit_graph_norm,
            "fit_graph_mc_sub": fit_graph_mc_sub,
        }, cs_expressions
    else:
        return {
            "fit_graph_slope": fit_graph_slope,
            "fit_graph_norm": fit_graph_norm,
        }, cs_expressions


def smooth_function(ff_hist, bin_edges):
    hist_bins = ff_hist.GetNbinsX()

    x = list()
    y = list()
    error_y_up = list()
    error_y_down = list()
    for nbin in range(hist_bins):
        x.append(ff_hist.GetBinCenter(nbin + 1))
        y.append(ff_hist.GetBinContent(nbin + 1))
        error_y_up.append(ff_hist.GetBinErrorUp(nbin + 1))
        error_y_down.append(ff_hist.GetBinErrorLow(nbin + 1))

    x = array.array("d", x)
    y = array.array("d", y)
    error_y_up = array.array("d", error_y_up)
    error_y_down = array.array("d", error_y_down)

    # sampling values for y based on a normal distribution with the measured statistical uncertainty
    n_samples = 20
    sampled_y = list()
    for idx in range(len(x)):
        sampled_y.append(np.random.normal(y[idx], error_y_up[idx], n_samples))
    sampled_y = np.array(sampled_y)
    sampled_y[sampled_y < 0.0] = 0.0

    # calculate widths
    fit_y_binned = list()

    n_bins = 100 * hist_bins
    for i in range(n_bins):
        fit_y_binned.append(list())

    eval_bin_edges, bin_step = np.linspace(
        bin_edges[0], bin_edges[-1], (n_bins + 1), retstep=True
    )
    bin_range = bin_edges[-1] - bin_edges[0]
    bin_half = bin_step / 2.0
    smooth_x = (eval_bin_edges + bin_half)[:-1]
    smooth_x = array.array("d", smooth_x)

    for sample in range(n_samples):
        y_arr = array.array("d", sampled_y[:, sample])
        graph = ROOT.TGraphAsymmErrors(len(x), x, y_arr, 0, 0, error_y_down, error_y_up)
        gs = ROOT.TGraphSmooth("normal")
        grout = gs.SmoothKern(graph, "normal", (bin_range / 3.0), n_bins, smooth_x)
        for i in range(n_bins):
            fit_y_binned[i].append(grout.GetPointY(i))

    smooth_y = list()
    smooth_y_up = list()
    smooth_y_down = list()

    for b in fit_y_binned:
        smooth_y.append(np.mean(b))
        smooth_y_up.append(np.std(b))
        smooth_y_down.append(np.std(b))

    smooth_y = array.array("d", smooth_y)
    smooth_y_up = array.array("d", smooth_y_up)
    smooth_y_down = array.array("d", smooth_y_down)

    corr_dict = {
        "edges": np.array(eval_bin_edges),
        "y": np.array(smooth_y),
        "up": np.array(smooth_y) + np.array(smooth_y_up),
        "down": np.array(smooth_y) - np.array(smooth_y_down),
    }

    smooth_graph = ROOT.TGraphAsymmErrors(
        len(smooth_x), smooth_x, smooth_y, 0, 0, smooth_y_down, smooth_y_up
    )
    return smooth_graph, corr_dict


def calculate_non_closure_correction(SRlike, ARlike):
    corr = SRlike["data_subtracted"].Clone()

    frac = ARlike["data_subtracted"].GetMaximum() / ARlike["data"].GetMaximum()
    predicted = ARlike["data_ff"].Clone()
    predicted.Scale(frac)

    corr.Divide(predicted)
    return corr, frac


def calculate_non_closure_correction_Wjets(SRlike, ARlike):
    corr = SRlike["Wjets"].Clone()
    predicted = ARlike["Wjets_ff"].Clone()
    corr.Divide(predicted)
    return corr


def calculate_non_closure_correction_ttbar(SRlike, ARlike):
    corr = SRlike["ttbar_J"].Clone()
    predicted = ARlike["ttbar_ff"].Clone()
    corr.Divide(predicted)
    return corr


def calculating_FF(rdf):
    import correctionlib

    correctionlib.register_pyroot_binding()

    ROOT.gInterpreter.ProcessLine(
        """
        float calc_ff(float pt, int njets, float mt, int nbtag) {
        if (njets > 2) {
            njets = 2;
        }
        if (nbtag > 2) {
            nbtag = 2;
        }
        auto qcd = correction::CorrectionSet::from_file("workdir/json_test_v3/et/fake_factors.json")->at("QCD_fake_factors");
        auto wjets = correction::CorrectionSet::from_file("workdir/json_test_v3/et/fake_factors.json")->at("Wjets_fake_factors");
        auto ttbar = correction::CorrectionSet::from_file("workdir/json_test_v3/et/fake_factors.json")->at("ttbar_fake_factors");
        auto frac = correction::CorrectionSet::from_file("workdir/json_test_v3/et/fake_factors.json")->at("process_fractions");
        float qcd_ff = 1.;
        float wjets_ff = 1.;
        float ttbar_ff = 1.;
        qcd_ff = qcd->evaluate({pt, njets});
        wjets_ff = wjets->evaluate({pt, njets});
        if (njets == 0) {
            njets = 1;
        }
        ttbar_ff = ttbar->evaluate({pt, njets});
        float qcd_frac = 1.;
        float wjets_frac = 1.;
        float ttbar_frac = 1.;
        qcd_frac = frac->evaluate({"QCD", mt, nbtag});
        wjets_frac = frac->evaluate({"Wjets", mt, nbtag});
        ttbar_frac = frac->evaluate({"ttbar", mt, nbtag});
        float full_ff = qcd_frac*qcd_ff+wjets_frac*wjets_ff+ttbar_frac*ttbar_ff;
        return full_ff;
        }"""
    )

    rdf = rdf.Define(
        "fake_factor",
        "calc_ff(pt_2,njets,mt_1,nbtag)",
    )

    return rdf


def eval_QCD_FF(rdf, config, for_correction=False):
    import correctionlib

    correctionlib.register_pyroot_binding()

    if not for_correction:
        ff_path = (
            "workdir/"
            + config["workdir_name"]
            + "/"
            + config["era"]
            + "/fake_factors/fake_factors_{}.json".format(config["channel"])
        )
    else:
        ff_path = (
            "workdir/"
            + config["workdir_name"]
            + "/"
            + config["era"]
            + "/corrections/{ch}/fake_factors_{ch}_for_corrections.json".format(
                ch=config["channel"]
            )
        )

    ROOT.gInterpreter.ProcessLine(
        "float calc_ff_qcd(float pt, int njets) {"
        + "float n_jets = njets;"
        + 'auto qcd = correction::CorrectionSet::from_file("{}")->at("QCD_fake_factors");'.format(
            ff_path
        )
        + "float qcd_ff;"
        + 'qcd_ff = qcd->evaluate({pt, n_jets, "nominal"});'
        + "return qcd_ff;"
        + "}"
    )

    rdf = rdf.Define(
        "QCD_fake_factor",
        "calc_ff_qcd(pt_2,njets)",
    )

    return rdf


def eval_Wjets_FF(rdf, config, for_correction=False):
    import correctionlib

    correctionlib.register_pyroot_binding()

    if not for_correction:
        ff_path = (
            "workdir/"
            + config["workdir_name"]
            + "/"
            + config["era"]
            + "/fake_factors/fake_factors_{}.json".format(config["channel"])
        )
    else:
        ff_path = (
            "workdir/"
            + config["workdir_name"]
            + "/"
            + config["era"]
            + "/corrections/{ch}/fake_factors_{ch}_for_corrections.json".format(
                ch=config["channel"]
            )
        )

    ROOT.gInterpreter.ProcessLine(
        "float calc_ff_wjets(float pt, int njets) {"
        + "float n_jets = njets;"
        + 'auto wjets = correction::CorrectionSet::from_file("{}")->at("Wjets_fake_factors");'.format(
            ff_path
        )
        + "float wjets_ff;"
        + 'wjets_ff = wjets->evaluate({pt, n_jets, "nominal"});'
        + "return wjets_ff;"
        + "}"
    )

    rdf = rdf.Define(
        "Wjets_fake_factor",
        "calc_ff_wjets(pt_2,njets)",
    )

    return rdf


def eval_ttbar_FF(rdf, config):
    import correctionlib

    correctionlib.register_pyroot_binding()

    ff_path = (
        "workdir/"
        + config["workdir_name"]
        + "/"
        + config["era"]
        + "/fake_factors/fake_factors_{}.json".format(config["channel"])
    )

    ROOT.gInterpreter.ProcessLine(
        "float calc_ff_ttbar(float pt, int njets) {"
        + "float n_jets = njets;"
        + 'auto ttbar = correction::CorrectionSet::from_file("{}")->at("ttbar_fake_factors");'.format(
            ff_path
        )
        + "float ttbar_ff;"
        + 'ttbar_ff = ttbar->evaluate({pt, n_jets, "nominal"});'
        + "return ttbar_ff;"
        + "}"
    )

    rdf = rdf.Define(
        "ttbar_fake_factor",
        "calc_ff_ttbar(pt_2,njets)",
    )

    return rdf
