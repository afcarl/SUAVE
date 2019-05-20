## @ingroup Methods-Aerodynamics-Common-Fidelity_Zero-Lift
# weissinger_vortex_lattice.py
# 
# Created:  Dec 2013, SUAVE Team
# Modified: Apr 2017, T. MacDonald
#           Oct 2017, E. Botero
#           Jun 2018, M. Clarke


# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

# package imports
import numpy as np 

# ----------------------------------------------------------------------
#  Weissinger Vortex Lattice
# ----------------------------------------------------------------------

## @ingroup Methods-Aerodynamics-Common-Fidelity_Zero-Lift
def weissinger_VLM(conditions,configuration,wing):
    """Uses the vortex lattice method to compute the lift coefficient and induced drag component
    Assumptions:
    None
    Source:
    An Introduction to Theoretical and Computational Aerodynamics by Jack Moran
    Inputs:
    wing.
      spans.projected                       [m]
      chords.root                           [m]
      chords.tip                            [m]
      sweeps.quarter_chord                  [radians]
      taper                                 [Unitless]
      twists.root                           [radians]
      twists.tip                            [radians]
      symmetric                             [Boolean]
      aspect_ratio                          [Unitless]
      areas.reference                       [m^2]
      vertical                              [Boolean]
    configuration.number_panels_spanwise    [Unitless]
    configuration.number_panels_chordwise   [Unitless]
    conditions.aerodynamics.angle_of_attack [radians]
    Outputs:
    Cl                                      [Unitless]
    Cd                                      [Unitless]
    Properties Used:
    N/A
    """ 

    #unpack
    span        = wing.spans.projected
    root_chord  = wing.chords.root
    tip_chord   = wing.chords.tip
    sweep       = wing.sweeps.quarter_chord
    taper       = wing.taper
    twist_rc    = wing.twists.root
    twist_tc    = wing.twists.tip
    sym_para    = wing.symmetric
    Sref        = wing.areas.reference
    orientation = wing.vertical
    
    n  = configuration.number_panels_spanwise
    
    # conditions
    aoa = conditions.aerodynamics.angle_of_attack
    
    # chord difference
    dchord = (root_chord-tip_chord)
    if sym_para is True :
        span = span/2
        
    deltax  = span/n    
    sin_aoa = np.sin(aoa)
    cos_aoa = np.cos(aoa)

    if orientation == False :
        # Determine if wing segments are defined  
        n_segments           = len(wing.Segments.keys())
        segment_vortex_index = np.zeros(n_segments)
        # If spanwise stations are setup
        if n_segments>0:
            # discretizing the wing sections into panels
            i             = np.arange(0,n)
            j             = np.arange(0,n+1)
            y_coordinates = (j)*deltax             
            segment_chord = np.zeros(n_segments)
            segment_twist = np.zeros(n_segments)
            segment_sweep = np.zeros(n_segments)
            segment_span  = np.zeros(n_segments)
            segment_chord_x_offset = np.zeros(n_segments)
            section_stations       = np.zeros(n_segments)
            
            # obtain chord and twist at the beginning/end of each segment
            for i_seg in range(n_segments):                
                segment_chord[i_seg]    = wing.Segments[i_seg].root_chord_percent*root_chord
                segment_twist[i_seg]    = wing.Segments[i_seg].twist
                segment_sweep[i_seg]    = wing.Segments[i_seg].sweeps.quarter_chord
                section_stations[i_seg] = wing.Segments[i_seg].percent_span_location*span
                
                if i_seg == 0:
                    segment_span[i_seg]           = 0.0
                    segment_chord_x_offset[i_seg] = 0.25*root_chord # weissinger uses quarter chord as reference
                else:
                    segment_span[i_seg]           = wing.Segments[i_seg].percent_span_location*span - wing.Segments[i_seg-1].percent_span_location*span
                    segment_chord_x_offset[i_seg] = segment_chord_x_offset[i_seg-1] + segment_span[i_seg]*np.tan(segment_sweep[i_seg-1])
            
            # shift spanwise vortices onto section breaks 
            for i_seg in range(n_segments):
                idx =  (np.abs(y_coordinates-section_stations[i_seg])).argmin()
                y_coordinates[idx] = section_stations[i_seg]
            
            # define y coordinates of horseshoe vortices      
            ya     = np.atleast_2d(y_coordinates[i])           
            yb     = np.atleast_2d(y_coordinates[i+1])          
            deltax = y_coordinates[i+1] - y_coordinates[i]
            xa     = np.zeros(n)
            x      = np.zeros(n)
            y      = np.zeros(n)
            twist_distri  = np.zeros(n)
            chord_distri = np.zeros(n)
            
            # define coordinates of horseshoe vortices and control points
            i_seg = 0
            for idx in range(n):
                twist_distri[idx] =  segment_twist[i_seg] + ((yb[0][idx] - deltax[idx]/2 - section_stations[i_seg]) * (segment_twist[i_seg+1] - segment_twist[i_seg])/segment_span[i_seg+1])     
                chord_distri[idx] =  segment_chord[i_seg] + ((yb[0][idx] - deltax[idx]/2 - section_stations[i_seg]) * (segment_chord[i_seg+1] - segment_chord[i_seg])/segment_span[i_seg+1])
                xa[idx]           = segment_chord_x_offset[i_seg] + (yb[0][idx] - deltax[idx]/2 - section_stations[i_seg])*np.tan(segment_sweep[i_seg])                                                    # computer quarter chord points for each horseshoe vortex
                x[idx]            = segment_chord_x_offset[i_seg] + (yb[0][idx] - deltax[idx]/2 - section_stations[i_seg])*np.tan(segment_sweep[i_seg])  + 0.5*chord_distri[idx]                         # computer three-quarter chord control points for each horseshoe vortex
                y[idx]            = (yb[0][idx] -  deltax[idx]/2)                
                
                if y_coordinates[idx] == wing.Segments[i_seg+1].percent_span_location*span: 
                    i_seg += 1                    
                if y_coordinates[idx+1] == span:
                    continue
                                  
            ya = np.atleast_2d(ya)  # y coordinate of start of horseshoe vortex on panel
            yb = np.atleast_2d(yb)  # y coordinate of end horseshoe vortex on panel
            xa = np.atleast_2d(xa)  # x coordinate of horseshoe vortex on panel
            x  = np.atleast_2d(x)   # x coordinate of control points on panel
            y  = np.atleast_2d(y)   # y coordinate of control points on panel
            
            RHS  = np.atleast_2d(np.sin(twist_distri+aoa))  
   
        else:   # no segments defined on wing 
            # discretizing the wing sections into panels 
            i              = np.arange(0,n)
            chord_distri = dchord/span*(span-(i+1)*deltax+deltax/2) + tip_chord
            twist_distri   = twist_rc + i/float(n)*(twist_tc-twist_rc)
            
            ya   = np.atleast_2d((i)*deltax)                                                # y coordinate of start of horseshoe vortex on panel
            yb   = np.atleast_2d((i+1)*deltax)                                              # y coordinate of end horseshoe vortex on panel
            xa   = np.atleast_2d(((i+1)*deltax-deltax/2)*np.tan(sweep) + 0.25*chord_distri) # x coordinate of horseshoe vortex on panel
            x    = np.atleast_2d(((i+1)*deltax-deltax/2)*np.tan(sweep) + 0.75*chord_distri) # x coordinate of control points on panel
            y    = np.atleast_2d(((i+1)*deltax-deltax/2))                                   # y coordinate of control points on panel 
                    
            RHS  = np.atleast_2d(np.sin(twist_distri+aoa))                                  
                
        
        A = (whav(x,y,xa.T,ya.T)-whav(x,y,xa.T,yb.T)\
            -whav(x,y,xa.T,-ya.T)+whav(x,y,xa.T,-yb.T))*0.25/np.pi
    
        # Vortex strength computation by matrix inversion
        T = np.linalg.solve(A.T,RHS.T).T
        
        # broadcast out A
        A_b = np.broadcast_to(A,(len(aoa),A.shape[0],A.shape[1]))
        
        # Calculating the effective velocty         
        A_v = (A_b.T*0.25/np.pi*T.T).T
        v   = np.sum(A_v,axis=1)
        
        Lfi = -T * (sin_aoa-v)
        Lfk =  T * cos_aoa 
        Lft = -Lfi * sin_aoa + Lfk * cos_aoa
        Dg  =  Lfi * cos_aoa + Lfk * sin_aoa
            
        L  = deltax * Lft
        D  = deltax * Dg
        
        # Total lift
        LT = np.atleast_2d(np.sum(L,axis=1)).T
        DT = np.atleast_2d(np.sum(D,axis=1)).T
        
        CL = 2*LT/(0.5*Sref)
        CD = 8*DT/(Sref)
        
        #cl = L/(0.5*chord_distri) 
        #cdi = D/(0.5*chord_distri)      
        
    else:
        
        CL = np.zeros_like(aoa)
        CD = np.zeros_like(aoa)  
         
        cl = 0.0 
        cdi = 0.0 
        
    return CL, CD

# ----------------------------------------------------------------------
#   Helper Functions
# ----------------------------------------------------------------------
def whav(x1,y1,x2,y2):
    """ Helper function of vortex lattice method      
        Inputs:
            x1,x2 -x coordinates of bound vortex
            y1,y2 -y coordinates of bound vortex
        Outpus:
            Cl_comp - lift coefficient
            Cd_comp - drag  coefficient       
        Assumptions:
            if needed
    """    

    use_base    = 1 - np.isclose(x1,x2)*1.
    no_use_base = np.isclose(x1,x2)*1.
    
    y1_y2 = y1-y2
    x1_x2 = x1-x2
    
    y1_y2[y1_y2==0] = 1E-32 
    x1_x2[x1_x2==0] = 1E-32
    
    whv = 1/(y1_y2)*(1+ (np.sqrt((x1_x2)**2+(y1_y2)**2)/(x1_x2)))*use_base + (1/(y1_y2))*no_use_base
    
    return whv