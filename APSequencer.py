from __future__ import with_statement
import sys
from functools import partial
from contextlib import contextmanager

#added 17/10/17
from _Framework.ModesComponent import AddLayerMode, MultiEntryMode, ModesComponent, CancellableBehaviour, AlternativeBehaviour, ReenterBehaviour, DynamicBehaviourMixin, ExcludingBehaviourMixin, EnablingModesComponent, LazyComponentMode



from _Framework.ModesComponent import ModesComponent, ImmediateBehaviour
from _Framework.Layer import Layer
from _Framework.SessionZoomingComponent import SessionZoomingComponent
from _Framework.Dependency import inject
from _Framework.Util import const, recursive_map
from _Framework.Dependency import inject
from _Framework.ComboElement import ComboElement, DoublePressElement, MultiElement, DoublePressContext
from _Framework.ButtonMatrixElement import ButtonMatrixElement 
from _Framework.SubjectSlot import subject_slot
from _Framework.Resource import PrioritizedResource

from _Framework.BackgroundComponent import BackgroundComponent, ModifierBackgroundComponent
from _Framework.Util import clamp, nop, mixin, const, recursive_map, NamedTuple, get_slice
from _Framework.ClipCreator import ClipCreator





from _APC.APC import APC
from _PushLegacy import Colors
from _PushLegacy.PlayheadElement import PlayheadElement
from _PushLegacy.GridResolution import GridResolution
from _PushLegacy.AutoArmComponent import AutoArmComponent



from _PushLegacy import consts
from _PushLegacy.SkinDefault import make_default_skin
from _PushLegacy.ControlElementFactory import create_button
from _PushLegacy.ViewControlComponent import ViewControlComponent
from _PushLegacy.StepSeqComponent import DrumGroupFinderComponent
from _APC.ControlElementUtils import make_button


# Monkeypatch things
import ControlElementUtils
import SkinDefault
import SessionComponent
sys.modules['_APC.ControlElementUtils'] = ControlElementUtils
sys.modules['_APC.SkinDefault'] = SkinDefault
sys.modules['_APC.SessionComponent'] = SessionComponent




from APC40_MkII.APC40_MkII import APC40_MkII, NUM_SCENES, NUM_TRACKS
#from SkinDefault import make_rgb_skin, make_default_skin, make_stop_button_skin, make_crossfade_button_skin
from SessionComponent import SessionComponent

from StepSeqComponent import StepSeqComponent

# added 15/10/17



from _PushLegacy.MelodicComponent import MelodicComponent


#cont

from MatrixMaps import PAD_TRANSLATIONS, FEEDBACK_CHANNELS
from ButtonSliderElement import ButtonSliderElement

from LooperComponent import LooperComponent      # added
from SelectComponent import SelectComponent      # added

class APSequencer(APC40_MkII):
  """ APC40Mk2 script with step sequencer mode """
  def __init__(self, *a, **k):
    self._double_press_context = DoublePressContext()
    APC40_MkII.__init__(self, *a, **k)
    with self.component_guard():

      self._skin = make_default_skin()
      self._clip_creator = ClipCreator()
      
      self._init_background()
      self._init_step_sequencer()
      self._init_instrument()
      
      
 
      self._init_matrix_modes() 
  
  

  
  
#      self._init_auto_arm()
    
      self._on_selected_track_changed()
    
    
    self.set_pad_translations(PAD_TRANSLATIONS)
    self.set_feedback_channels(FEEDBACK_CHANNELS)

  
  
  def _create_controls(self):
    """ Add some additional stuff baby """
    super(APSequencer, self)._create_controls()
    self._grid_resolution = GridResolution()
    self._velocity_slider = ButtonSliderElement(tuple(self._scene_launch_buttons_raw[::-1])) 
    

    
    double_press_rows = recursive_map(DoublePressElement, self._matrix_rows_raw) 
    self._double_press_matrix = ButtonMatrixElement(name='Double_Press_Matrix', rows=double_press_rows)
    self._double_press_event_matrix = ButtonMatrixElement(name='Double_Press_Event_Matrix', rows=recursive_map(lambda x: x.double_press, double_press_rows))
    self._playhead = PlayheadElement(self._c_instance.playhead)

    # Make these prioritized resources, which share between Layers() equally
    # Rather than building a stack
    self._pan_button._resource_type = PrioritizedResource 
    self._user_button._resource_type = PrioritizedResource 
    


    
    
    self._view_control = ViewControlComponent(name='View_Control')
    self._view_control.set_enabled(False)
 
 
  def _init_background(self):
      self._background = BackgroundComponent(is_root=True)
      self._background.layer = Layer(velocity_slider = self._velocity_slider)#, display_line2=self._display_line2, display_line3=self._display_line3, display_line4=self._display_line4, top_buttons=self._select_buttons, bottom_buttons=self._track_state_buttons, scales_button=self._scale_presets_button, octave_up=self._octave_up_button, octave_down=self._octave_down_button, side_buttons=self._side_buttons, repeat_button=self._repeat_button, accent_button=self._accent_button, double_button=self._double_button, in_button=self._in_button, out_button=self._out_button, param_controls=self._global_param_controls, param_touch=self._global_param_touch_buttons, tempo_control_tap=self._tempo_control_tap, master_control_tap=self._master_volume_control_tap, touch_strip=self._touch_strip_control, touch_strip_tap=self._touch_strip_tap, nav_up_button=self._nav_up_button, nav_down_button=self._nav_down_button, nav_left_button=self._nav_left_button, nav_right_button=self._nav_right_button, aftertouch=self._aftertouch_control, pad_parameters=self._pad_parameter_control, _notification=self._notification.use_single_line(2), priority=consts.BACKGROUND_PRIORITY)
      self._matrix_background = BackgroundComponent()
      self._matrix_background.set_enabled(False)
      self._matrix_background.layer = Layer(matrix=self._session_matrix)
   #   self._mod_background = ModifierBackgroundComponent(is_root=True)
   #   self._mod_background.layer = Layer(shift_button=self._shift_button, select_button=self._select_button, delete_button=self._delete_button, duplicate_button=self._duplicate_button, quantize_button=self._quantize_button)
 
 
 
 
  def _init_step_sequencer(self):
    self._step_sequencer = StepSeqComponent(grid_resolution = self._grid_resolution)
    self._step_sequencer.layer = self._create_step_sequencer_layer()
  
  """lew saturday. works """
#  def _init_instrument(self):
#    self._instrument = MelodicComponent(grid_resolution = self._grid_resolution)
#    self._instrument.layer = self._create_instument_layer()
  
  
  """lew sunday"""
  def _init_instrument(self):
    instrument_basic_layer = Layer(
    #octave_strip=self._with_shift(self._touch_strip_control), 
   # scales_toggle_button=self._tap_tempo_button, 
    octave_up_button=self._up_button, octave_down_button=self._down_button, 
    scale_up_button=self._with_shift(self._up_button), 
    scale_down_button=self._with_shift(self._down_button))
    self._instrument = MelodicComponent(skin=self._skin, is_enabled=False, 
    clip_creator=self._clip_creator, name='Melodic_Component', 
    grid_resolution=self._grid_resolution, 
    #note_editor_settings=self._add_note_editor_setting(), 
    layer=self._create_instrument_layer(), instrument_play_layer=instrument_basic_layer + Layer(matrix=self._session_matrix), 
    #touch_strip=self._touch_strip_control, touch_strip_indication=self._with_firmware_version(1, 16, ComboElement(self._touch_strip_control, modifiers=[self._select_button])), 
    #touch_strip_toggle=self._with_firmware_version(1, 16, ComboElement(self._touch_strip_tap, modifiers=[self._select_button])), 
    #aftertouch_control=self._aftertouch_control, delete_button=self._delete_button), 
    instrument_sequence_layer=instrument_basic_layer)# + Layer(note_strip=self._touch_strip_control))
    self._on_note_editor_layout_changed.subject = self._instrument








  
  def _init_matrix_modes(self):
    """ Switch between Session and StepSequencer modes """
    
 
 
   
    """here we go trying to switch.... lew  05:53   21/10/17"""
    
    self._auto_arm = AutoArmComponent(name='Auto_Arm')
    
    self._drum_group_finder = DrumGroupFinderComponent()
    self._on_drum_group_changed.subject = self._drum_group_finder
    
    
    self._drum_modes = ModesComponent(name='Drum_Modes', is_enabled=False)
    self._drum_modes.add_mode('sequencer', self._step_sequencer)   
    self._drum_modes.selected_mode = 'sequencer'
   
    self._note_modes = ModesComponent(name='Note_Modes')#, is_enabled=False)
    self._note_modes.add_mode('drums', [self._drum_modes])
    self._drum_modes.selected_mode = 'sequencer'
    self._note_modes.add_mode('looper', self._audio_loop if consts.PROTO_AUDIO_NOTE_MODE else self._matrix_background)
    self._note_modes.add_mode('instrument', self._instrument)
    self._note_modes.add_mode('disabled', self._matrix_background)
    self._note_modes.selected_mode = 'disabled'    
    self._note_modes.set_enabled(False)
   
   
    #self._note_modes.add_mode('sequencer', self._step_sequencer)  
    
    
   
    
    
    
    
    def switch_note_mode_layout():
      if self._note_modes.selected_mode == 'instrument':
        getattr(self._instrument, 'cycle_mode', nop)()
      elif self._note_modes.selected_mode == 'drums':
        getattr(self._drum_modes, 'cycle_mode', nop)()    
    
    
    self._matrix_modes = ModesComponent(name='Matrix_Modes', is_root=True)
    self._matrix_modes.add_mode('session', self._session_mode_layers())
    self._matrix_modes.add_mode('note', [self._drum_group_finder, self._view_control, self._note_modes],behaviour=self._auto_arm.auto_arm_restore_behaviour(ReenterBehaviour, on_reenter=switch_note_mode_layout))
    
    self._matrix_modes.selected_mode = 'note'
    self._matrix_modes.layer = Layer(session_button=self._pan_button, note_button=self._user_button)
    
    self._on_matrix_mode_changed.subject = self._matrix_modes   # (errors begin)
    self._matrix_modes.selected_mode = 'note'
 







  

    #added for looping capability
    #self._looper = LooperComponent(self)               
    #self._looper.name = 'looper_Component'    
    
  
    
    
  
  
  
  def _session_mode_layers(self):
    return [ self._session, self._session_zoom]

  def _create_step_sequencer_layer(self):
    return Layer(
        velocity_slider = self._velocity_slider,
        drum_matrix = self._session_matrix.submatrix[:4, 1:5],  # [4, 1:5],  mess with this for possible future 32 pad drum rack :
     

        button_matrix = self._double_press_matrix.submatrix[4:8, 1:5],   # [4:8, 1:5],
        
      #  next_page_button = self._bank_button,
        
        select_button = self._user_button,
        delete_button = self._stop_all_button,
        playhead = self._playhead,
        quantization_buttons = self._stop_buttons,
        shift_button = self._shift_button,
        loop_selector_matrix = self._double_press_matrix.submatrix[:4, :1],                # changed from [:8, :1] so as to enable bottem row of rack   . second value clip length rows
        short_loop_selector_matrix = self._double_press_event_matrix.submatrix[:4, :1],     # changed from [:8, :1] no change noticed as of yet   
        octave_up_button=self._up_button, octave_down_button=self._down_button 
        #drum_bank_up_button = self._up_button,drum_bank_down_button = self._down_button
        )

  """lew saturday. works"""  
#  def _create_instument_layer(self):
#          return Layer(
#            playhead=self._playhead, #mute_button=self._global_mute_button, 
#            quantization_buttons=self._stop_buttons, 
            #octave_up_button=self._nudge_up_button, octave_down_button=self._down_button,    #      keep commented out
#            loop_selector_matrix=self._double_press_matrix.submatrix[:8, :2], #[:, 0],
#            short_loop_selector_matrix=self._double_press_event_matrix.submatrix[:8, :1], #[:, 0],
#            note_editor_matrices=ButtonMatrixElement([[ self._session_matrix.submatrix[:, 4 - row] for row in xrange(7) ]]))   #self._session_matrix.submatrix[:, 7 - row] for row in xrange(7)
    
 
  
  
  """lew sunday"""
  
  def _create_instrument_layer(self):
    return Layer(
      playhead=self._playhead, 
      #mute_button=self._global_mute_button, 
      quantization_buttons=self._stop_buttons, 
      loop_selector_matrix=self._double_press_matrix.submatrix[:8, :1],# [:, 0]
      short_loop_selector_matrix=self._double_press_event_matrix.submatrix[:, 0],# [:, 0]
      note_editor_matrices=ButtonMatrixElement([[ self._session_matrix.submatrix[:, 4 - row] for row in xrange(7) ]]))
      #note_editor_matrices=ButtonMatrixElement([[ self._session_matrix.submatrix[:, 7 - row] for row in xrange(7) ]]))
  
  
  
  
  

  
  
  
  
  
  def _session_layer(self):
    def when_bank_on(button):
      return self._bank_toggle.create_toggle_element(on_control=button)
    def when_bank_off(button):
      return self._bank_toggle.create_toggle_element(off_control=button)
    return Layer(
      track_bank_left_button = when_bank_off(self._left_button), 
      track_bank_right_button = when_bank_off(self._right_button), 
      scene_bank_up_button = when_bank_off(self._up_button), 
      scene_bank_down_button = when_bank_off(self._down_button), 
      page_left_button = when_bank_on(self._left_button), 
      page_right_button = when_bank_on(self._right_button), 
      page_up_button = when_bank_on(self._up_button), 
      page_down_button = when_bank_on(self._down_button), 
      stop_track_clip_buttons = self._stop_buttons,
      stop_all_clips_button = self._stop_all_button, 
      scene_launch_buttons = self._scene_launch_buttons, 
      clip_launch_buttons = self._session_matrix)

  def _session_zoom_layer(self):
    return Layer(button_matrix=self._shifted_matrix, 
      nav_left_button=self._with_shift(self._left_button), 
      nav_right_button=self._with_shift(self._right_button), 
      nav_up_button=self._with_shift(self._up_button), 
      nav_down_button=self._with_shift(self._down_button), 
      scene_bank_buttons=self._shifted_scene_buttons)

  
  @subject_slot('selected_mode')
  def _on_matrix_mode_changed(self, mode):
      self._update_auto_arm(selected_mode=mode)  
  
  
  def _update_auto_arm(self, selected_mode = None):
      self._auto_arm.set_enabled(selected_mode or self._matrix_modes.selected_mode == 'note')  
  
#  def _init_auto_arm(self):                                                # swap above lew 22/10/17
 #   self._auto_arm = AutoArmComponent(is_enabled = True)

  
  
  @subject_slot('drum_group')
  def _on_drum_group_changed(self):
      self._select_note_mode()


  def _select_note_mode(self):
    """
    Selects which note mode to use depending on the kind of
    current selected track and its device chain...
    """
    track = self.song().view.selected_track
    drum_device = self._drum_group_finder.drum_group
    self._step_sequencer.set_drum_group_device(drum_device)
    #self._drum_component.set_drum_group_device(drum_device)
    if track == None or track.is_foldable or track in self.song().return_tracks or track == self.song().master_track or track.is_frozen:
      self._note_modes.selected_mode = 'disabled'
    elif track and track.has_audio_input:
      self._note_modes.selected_mode = 'looper'
    elif drum_device:
      self._note_modes.selected_mode = 'drums'
    else:
      self._note_modes.selected_mode = 'instrument'
    self.reset_controlled_track()




  # added so as to have looping with pan_button held
#    self._select_modes = SelectComponent(self, tuple(self._raw_select_buttons), self._metronome_button, self._nudge_down_button, self._nudge_up_button, self._tap_tempo_button, self._transport, self._looper, self._session, self._session_matrix) 
#    self._select_modes.name = 'Select_Modes'
#    self._select_modes.set_mode_toggle(self._pan_button)  
  
  
  
  
  
  # commented to test 0:47 
  
  # EVENT HANDLING FUNCTIONS
 # def reset_controlled_track(self):
   # self.set_controlled_track(self.song().view.selected_track)
  
  
  
  """lew sunday"""
  
  
  
  @subject_slot('selected_mode')
  def _on_note_editor_layout_changed(self, mode):
      self.reset_controlled_track(mode)  
  
  
  
  
  
  def reset_controlled_track(self, mode = None):
    if mode == None:
      mode = self._instrument.selected_mode
    if self._instrument.is_enabled() and mode == 'sequence':
      self.release_controlled_track()
    else:
      self.set_controlled_track(self.song().view.selected_track)  
  
  
  
  
    self.drum_pads_scroll_position
  
  
  
  def update(self):
    self.reset_controlled_track()
    self.set_feedback_channels(FEEDBACK_CHANNELS)  # push added line
    super(APSequencer, self).update()

  
  
  
  def _on_selected_track_changed(self):
      super(APSequencer, self)._on_selected_track_changed()
      self.reset_controlled_track()
      self._select_note_mode()
  #    self._main_modes.pop_groups(['add_effect'])
  #    self._note_repeat_enabler.selected_mode = 'disabled'  
  
  
  
  
  
  
 # apc orig 
  
  
#  def _on_selected_track_changed(self):
#    self.reset_controlled_track()
#    if self._auto_arm.needs_restore_auto_arm:
#      self.schedule_message(1, self._auto_arm.restore_auto_arm)
#    super(APSequencer, self)._on_selected_track_changed()

  @contextmanager
  def component_guard(self):
    """ Customized to inject additional things """
    with super(APSequencer, self).component_guard():
      with self.make_injector().everywhere():
        yield

  def make_injector(self):
    """ Adds some additional stuff to the injector, used in BaseMessenger """
    return inject(
      double_press_context = const(self._double_press_context),
      control_surface = const(self),
     
      log_message = const(self.log_message))







# ##    ok from here 08:22 22/10/17
# ##