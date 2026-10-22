extends SceneTree
func _initialize():call_deferred("run")
func run():
 var s=root.get_node("GameState");s.persist=false
 var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
 var d=root.get_node("Director");var h=d.world;var u=d.ui
 u.menus.hide();u.eyelids_set(1);s.reset();s.shot="C4-03"
 h.show_scene("greenhouse");h.apply_room_states("C4-03");h.set_mode("walk","");u.set_cinematic(false)
 await physics_frame;await physics_frame
 var target=h.hotspot_nodes["hs_gh_photos"]
 print("PHOTO hotspot=",target.global_position," visible=",target.is_visible_in_tree())
 print("PHOTO guide target=",h.target_position("hs_gh_photos"))
 var g=load("res://world/guide.gd").new();g.host=h;h.add_child(g);await g._ensure_mesh()
 for p in [Vector3(21.4,3.631,-9),Vector3(21.6985,3.659,-7.6315),Vector3(20.5,3.63,-10)]:
  h.player.place(p,0);await physics_frame;await physics_frame
  var t=h.target_position("hs_gh_photos")
  var start=g._poly_at(h.player.global_position);var goal=g._poly_at(t)
  var floor_goal=g._poly_at(Vector3(t.x,3.63,t.z))
  print("NAV feet=",h.player.global_position," start=",start," target=",t," goal=",goal," floor_goal=",floor_goal)
  print("NAV show actual=",await g.show_path([t])," floor=",await g.show_path([Vector3(t.x,3.63,t.z)]))
 h.player.place(Vector3(21.4,3.63,-9.1),0);h.player.frozen=true
 h.highlight_hotspots(["hs_gh_photos"])
 await physics_frame;await physics_frame
 var delta:Vector3=target.global_position-h.player.cam.global_position
 h.player.rotation.y=atan2(-delta.x,-delta.z);h.player._pitch=atan2(delta.y,Vector2(delta.x,delta.z).length());h.player.cam.look_at(target.global_position);h.player._update_hover()
 print("AIM hover=",h.player._hover," camera=",h.player.cam.global_position)
 var sight=h.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(h.player.cam.global_position,target.global_position,1))
 print("SIGHT blocker=",sight.get("collider").get_path() if sight.has("collider") else "none"," hit=",sight.get("position"))

 var q=PhysicsRayQueryParameters3D.create(target.global_position+Vector3.UP*.1,target.global_position+Vector3.DOWN*3,1)
 var hit=h.get_world_3d().direct_space_state.intersect_ray(q)
 print("RAY ",hit.get("position")," collider=",hit.get("collider").get_path())
 for n in h._walk(h.room):
  if String(n.name)=="夜拍照片":
   print("DOCUMENT ",n.get_path()," at=",n.global_position," rotation=",n.global_rotation_degrees," visible=",n.is_visible_in_tree())
 print("VIEW yaw=",h.player.rotation_degrees.y," pitch=",rad_to_deg(h.player._pitch))
 if not OS.has_feature("headless"):
  await create_timer(1).timeout;await RenderingServer.frame_post_draw
  get_root().get_texture().get_image().save_png("/tmp/pr34-photo-location.png")
 main.queue_free();await process_frame;quit()
