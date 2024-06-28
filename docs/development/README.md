# Development

## Animations

### Adding Animation

To add anmiation create class in ```src\controller\strip\modes``` inheriting from ```mode``` class.

After implementing mode, open ```mode_manager```, import mode class and add it to list of modes ```self._modes```.

Then opern ```state_manager``` and increase ```MAX_MODE_ID``` property
