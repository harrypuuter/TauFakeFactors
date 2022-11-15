"""
Function for calculating fake factors for the ttbar process
"""

import array
import ROOT

from helper import region_filters as filters
import helper.functions as func
import helper.plotting as plotting


def calculation_ttbar_FFs(config, sample_path_list):
    # init histogram dict for FF measurement from MC
    SR_hists = dict()
    AR_hists = dict()
    # init histogram dict for FF data correction
    SRlike_hists = dict()
    ARlike_hists = dict()
    # init histogram dict for QCD SS/OS estimation
    SRlike_hists_qcd = dict()
    ARlike_hists_qcd = dict()

    process_conf = config["target_process"]["ttbar"]

    # calculating global histograms for the data/mc scale factor
    for sample_path in sample_path_list:
        # getting the name of the process from the sample path
        sample = sample_path.rsplit("/")[-1].rsplit(".")[0]
        print("Processing {} for the ttbar global data/mc scale factor.".format(sample))
        print("-" * 50)

        rdf = ROOT.RDataFrame(config["tree"], sample_path)

        njets = ">= 0"  # inclusive
        # event filter for ttbar signal-like region
        region_cut_conf = process_conf["SRlike_cuts"]
        rdf_SRlike = filters.btag_number(rdf, config["channel"], region_cut_conf)
        rdf_SRlike = filters.no_extra_leptons(
            rdf_SRlike, config["channel"], region_cut_conf
        )
        rdf_SRlike = filters.tau_id_vs_jets_WP(
            rdf_SRlike, config["channel"], region_cut_conf
        )
        rdf_SRlike = filters.jet_number(rdf_SRlike, config["channel"], njets)
        # split into same/opposite sign regions for QCD estimation
        rdf_SRlike_qcd = filters.same_opposite_sign(
            rdf_SRlike, config["channel"], "same"
        )
        rdf_SRlike = filters.same_opposite_sign(
            rdf_SRlike, config["channel"], region_cut_conf["tau_pair_sign"]
        )

        print(
            "Filtering events for the signal-like region. Target process: {}\n".format(
                "ttbar"
            )
        )
        rdf_SRlike.Report().Print()
        print("-" * 50)

        # event filter for ttbar application-like region
        region_cut_conf = process_conf["ARlike_cuts"]
        rdf_ARlike = filters.btag_number(rdf, config["channel"], region_cut_conf)
        rdf_ARlike = filters.no_extra_leptons(
            rdf_ARlike, config["channel"], region_cut_conf
        )
        rdf_ARlike = filters.tau_id_vs_jets_between_WPs(
            rdf_ARlike, config["channel"], region_cut_conf
        )
        rdf_ARlike = filters.jet_number(rdf_ARlike, config["channel"], njets)
        # split into same/opposite sign regions for QCD estimation
        rdf_ARlike_qcd = filters.same_opposite_sign(
            rdf_ARlike, config["channel"], "same"
        )
        rdf_ARlike = filters.same_opposite_sign(
            rdf_ARlike, config["channel"], region_cut_conf["tau_pair_sign"]
        )

        print(
            "Filtering events for the application-like region. Target process: {}\n".format(
                "ttbar"
            )
        )
        rdf_ARlike.Report().Print()
        print("-" * 50)

        # make yield histograms for FF data correction
        h = rdf_SRlike.Histo1D(
            ("#phi(#tau_{h})", "{}".format(sample), 1, -3.5, 3.5), "phi_2", "weight"
        )
        SRlike_hists[sample] = h.GetValue()
        h = rdf_ARlike.Histo1D(
            ("#phi(#tau_{h})", "{}".format(sample), 1, -3.5, 3.5), "phi_2", "weight"
        )
        ARlike_hists[sample] = h.GetValue()
        # make yield histograms for QCD estimation
        h_qcd = rdf_SRlike_qcd.Histo1D(
            ("#phi(#tau_{h})", "{}".format(sample), 1, -3.5, 3.5), "phi_2", "weight"
        )
        SRlike_hists_qcd[sample] = h_qcd.GetValue()
        h_qcd = rdf_ARlike_qcd.Histo1D(
            ("#phi(#tau_{h})", "{}".format(sample), 1, -3.5, 3.5), "phi_2", "weight"
        )
        ARlike_hists_qcd[sample] = h_qcd.GetValue()

    # calculate QCD estimation
    SRlike_hists["QCD"] = func.QCD_SS_estimate(SRlike_hists_qcd)
    ARlike_hists["QCD"] = func.QCD_SS_estimate(ARlike_hists_qcd)

    # calculate ttbar enriched data by subtraction all there backgrould sample
    SRlike_hists["data_subtracted"] = SRlike_hists["data"].Clone()
    ARlike_hists["data_subtracted"] = ARlike_hists["data"].Clone()

    for hist in SRlike_hists:
        if hist not in ["data", "data_subtracted", "ttbar_J"] and "_T" not in hist:
            SRlike_hists["data_subtracted"].Add(SRlike_hists[hist], -1)
    for hist in ARlike_hists:
        if hist not in ["data", "data_subtracted", "ttbar_J"] and "_T" not in hist:
            ARlike_hists["data_subtracted"].Add(ARlike_hists[hist], -1)

    # differentiating between N_jets categories for mc-based FF calculation
    for njets in process_conf["njet_split_categories"]:
        for sample_path in sample_path_list:
            # getting the name of the process from the sample path
            sample = sample_path.rsplit("/")[-1].rsplit(".")[0]
            # FFs for ttbar from mc -> only ttbar with true misindentified jets relevant
            if sample == "ttbar_J":
                print("Processing {} for the {} jets category.".format(sample, njets))
                print("-" * 50)

                rdf = ROOT.RDataFrame(config["tree"], sample_path)

                # event filter for ttbar signal region
                region_cut_conf = process_conf["SR_cuts"]
                rdf_SR = filters.same_opposite_sign(
                    rdf, config["channel"], region_cut_conf["tau_pair_sign"]
                )
                rdf_SR = filters.btag_number(rdf_SR, config["channel"], region_cut_conf)
                rdf_SR = filters.no_extra_leptons(
                    rdf_SR, config["channel"], region_cut_conf
                )
                rdf_SR = filters.tau_id_vs_jets_WP(
                    rdf_SR, config["channel"], region_cut_conf
                )
                rdf_SR = filters.jet_number(rdf_SR, config["channel"], njets)

                print(
                    "Filtering events for the signal region. Target process: {}\n".format(
                        "ttbar"
                    )
                )
                rdf_SR.Report().Print()
                print("-" * 50)

                # event filter for ttbar application region
                region_cut_conf = process_conf["AR_cuts"]
                rdf_AR = filters.same_opposite_sign(
                    rdf, config["channel"], region_cut_conf["tau_pair_sign"]
                )
                rdf_AR = filters.btag_number(rdf_AR, config["channel"], region_cut_conf)
                rdf_AR = filters.no_extra_leptons(
                    rdf_AR, config["channel"], region_cut_conf
                )
                rdf_AR = filters.tau_id_vs_jets_between_WPs(
                    rdf_AR, config["channel"], region_cut_conf
                )
                rdf_AR = filters.jet_number(rdf_AR, config["channel"], njets)

                print(
                    "Filtering events for the application region. Target process: {}\n".format(
                        "ttbar"
                    )
                )
                rdf_AR.Report().Print()
                print("-" * 50)

                # get binning for tau pT
                xbinning = array.array("d", process_conf["tau_pt_bins"])
                nbinsx = len(process_conf["tau_pt_bins"]) - 1
                # make tau pT histograms

                h = rdf_SR.Histo1D(
                    ("p_{T}(#tau_{h})", "{}".format(sample), nbinsx, xbinning),
                    "pt_2",
                    "weight",
                )
                SR_hists[sample] = h.GetValue()
                h = rdf_AR.Histo1D(
                    ("p_{T}(#tau_{h})", "{}".format(sample), nbinsx, xbinning),
                    "pt_2",
                    "weight",
                )
                AR_hists[sample] = h.GetValue()

        # Start of the calculation
        FF_hist = func.calculate_ttbar_FF(
            SR_hists, AR_hists, SRlike_hists, ARlike_hists
        )
        plotting.plot_FFs(FF_hist, config, "ttbar", njets)

        sig = "data"
        bkg = [
            "QCD",
            "diboson_J",
            "diboson_L",
            "Wjets",
            "ttbar_J",
            "ttbar_L",
            "DYjets_J",
            "DYjets_L",
            "embedding",
        ]
        # plotting.plot_data_mc(SRlike_hists, config, "SR_like", "tau_phi", "ttbar", njets, sig, bkg)
        # plotting.plot_data_mc(ARlike_hists, config, "AR_like", "tau_phi", "ttbar", njets, sig, bkg)
        plotting.plot_data_mc_ratio(
            SRlike_hists, config, "SR_like", "tau_phi", "ttbar", njets, sig, bkg
        )
        plotting.plot_data_mc_ratio(
            ARlike_hists, config, "AR_like", "tau_phi", "ttbar", njets, sig, bkg
        )
        sig = "data_subtracted"
        bkg = ["ttbar_J"]
        # plotting.plot_data_mc(SRlike_hists, config, "SR_like", "tau_phi", "ttbar", njets, sig, bkg)
        # plotting.plot_data_mc(ARlike_hists, config, "AR_like", "tau_phi", "ttbar", njets, sig, bkg)
        plotting.plot_data_mc_ratio(
            SRlike_hists, config, "SR_like", "tau_phi", "ttbar", njets, sig, bkg
        )
        plotting.plot_data_mc_ratio(
            ARlike_hists, config, "AR_like", "tau_phi", "ttbar", njets, sig, bkg
        )
