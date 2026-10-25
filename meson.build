project('nusa', 'cpp',
  version : '0.1.0',
  meson_version : '>=0.59.0',
  default_options : ['warning_level=1']
)

# Pulse is a Pure Python + GLib/GTK4 application. There are no compiled
# sources to link, so meson's job is only to install the package and the
# data files the app needs at runtime.

python3 = find_program('python3', required : true)

# Runtime data (config + package + sample music + icons) lands under
# ${datadir}/nusa/ so the app can resolve paths from the installed tree.
install_data('config.json', install_dir : get_option('datadir') / 'nusa')
install_subdir('src', install_dir : get_option('datadir') / 'nusa')
install_subdir('src/resources/data/music', install_dir : get_option('datadir') / 'nusa' / 'data' / 'music')
install_subdir('src/resources/icons', install_dir : get_option('datadir') / 'nusa' / 'icons')
install_data('pulse.desktop', install_dir : get_option('datadir') / 'applications')
