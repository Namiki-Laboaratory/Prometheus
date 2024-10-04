# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Prometheus",
    "author" : "J_Orange",
    "description" : "Auto generate realistic rendering dataset",
    "blender" : (3, 2, 1),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Dataset"
}

import bpy

from . import util, opt, props, ui

classes = util.Register  + opt.AllOperators + props.AllPropClasses + ui.AllPanelClasses

def register():
    for c in classes:
        bpy.utils.register_class(c)
    
    bpy.types.Scene.P_S = bpy.props.PointerProperty(type=props.Props_All)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.P_S