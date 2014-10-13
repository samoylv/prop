def get_beamline():
    from wpg import Wavefront
    import wpg.optical_elements
    from wpg.optical_elements import Use_PP

    distance = 300.
    foc_dist = 2.
    drift0 = wpg.optical_elements.Drift(distance)
    lens0  = wpg.optical_elements.Lens(foc_dist, foc_dist)
    drift1 = wpg.optical_elements.Drift(1./(1./foc_dist-1./distance))
    ##srwl_bl0 = SRWLOptC([drift0, ], [Use_PP(semi_analytical_treatment=1,zoom=0.1,sampling=4)])
    ##bl0 = wpg.Beamline(srwl_bl0)

    bl0 = wpg.Beamline()
    bl0.append(drift0, Use_PP(semi_analytical_treatment=1, zoom=0.50, sampling=8))
    bl0.append(lens0,  Use_PP())
    bl0.append(drift1, Use_PP(semi_analytical_treatment=1, zoom=4.2,  sampling=0.5))

    return bl0