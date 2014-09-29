import sys
from itertools import chain, imap, ifilter
from _Framework.SubjectSlot import subject_slot, subject_slot_group
from Push.NoteEditorComponent import NoteEditorComponent, most_significant_note

def color_for_note(note):
  velocity = note[3]
  muted = note[4]
  if not muted:
    if velocity == 127:
      return 'Full'
    elif velocity >= 94:
      return 'High'
    elif velocity >= 62:
      return 'Medium'
    elif velocity >= 31:
      return "Low"
    else:
      return 'Empty'
  else:
    return 'Muted'

class APCNoteEditorComponent(NoteEditorComponent):
  """ Customized to have a ButtonSlider for adjustable velocity 
  And adds some possible colors to note velocity display
  """

  def _add_note_in_step(self, step, modify_existing = True):
    """
    Add note in given step if there are none in there, otherwise
    select the step for potential deletion or modification

    Overriden to use self.velocity
    """
    if self._sequencer_clip != None:
      x, y = step
      time = self._get_step_start_time(x, y)
      notes = self._time_step(time).filter_notes(self._clip_notes)
      if notes:
        if modify_existing:
          most_significant_velocity = most_significant_note(notes)[3]
          if self._mute_button and self._mute_button.is_pressed() or most_significant_velocity != 127 and self.full_velocity:
            self._trigger_modification(step, immediate=True)
      else:
        pitch = self._note_index
        mute = self._mute_button and self._mute_button.is_pressed()
        velocity = 127 if self.full_velocity else self._velocity
        note = (pitch,
         time,
         self._get_step_length(),
         velocity,
         mute)
        self._sequencer_clip.set_notes((note,))
        self._sequencer_clip.deselect_all_notes()
        self._trigger_modification(step, done=True)
        return True
    return False


  def _update_editor_matrix(self):
    """
    update offline array of button LED values, based on note
    velocity and mute states
    """
    step_colors = ['NoteEditor.StepDisabled'] * self._get_step_count()
    width = self._width
    coords_to_index = lambda (x, y): x + y * width
    editing_indices = set(map(coords_to_index, self._modified_steps))
    selected_indices = set(map(coords_to_index, self._pressed_steps))
    last_editing_notes = []
    for time_step, index in self._visible_steps():
      notes = time_step.filter_notes(self._clip_notes)
      if len(notes) > 0:
        last_editing_notes = []
        if index in selected_indices:
          color = 'NoteEditor.StepSelected'
        elif index in editing_indices:
          note_color = color_for_note(most_significant_note(notes))
          color = 'NoteEditor.StepEditing.' + note_color
          last_editing_notes = notes
        else:
          note_color = color_for_note(most_significant_note(notes))
          color = 'NoteEditor.Step.' + note_color
      elif any(imap(time_step.overlaps_note, last_editing_notes)):
        color = 'NoteEditor.StepEditing.' + note_color
      elif index in editing_indices or index in selected_indices:
        color = 'NoteEditor.StepSelected'
        last_editing_notes = []
      else:
        color = self.background_color
        last_editing_notes = []
      step_colors[index] = color

    self._step_colors = step_colors
    self._update_editor_matrix_leds()


  def set_velocity_slider(self, button_slider):
    self._velocity_slider = button_slider
    self._on_velocity_changed.subject = button_slider
    self._update_velocity_slider()

  def _update_velocity_slider(self):
    if hasattr(self, "_velocity_slider") and self._velocity_slider:
      self._velocity_slider.send_value(self._velocity)
  
  @subject_slot("value")
  def _on_velocity_changed(self, value):
    self._velocity = value
    self._update_velocity_slider()

  def update(self):
    super(NoteEditorComponent, self).update()
    self._update_velocity_slider()