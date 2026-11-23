/**
 * adjustable-ft-v22-spring-clearance.scad
 *
 * 【V22：ばね干渉クリアランス完全解決版】
 * - [重要修正] 内輪が傾いた際に「ばね」がハンドプレート下面に激突する問題を解決
 * - ハンドプレートの裏面（ばねの直上）に、ばねの跳ね上がりを逃がすすり鉢状のテーパーを追加
 * - コネクタ逃げ空間とルーティング溝はV21の最適化寸法を維持
 */

eps = 0.01;
fn  = 150; 

// ==========================================
// 表示・出力オプション
// ==========================================
make_base_ring       = true;
make_hand_base_plate = false; 
make_stopper_ring    = false; 
make_test_cut        = false; 

explode_hand = 0; 
use_colors   = true;

// ==========================================
// 主要寸法パラメータ（V17極限コンパクト準拠）
// ==========================================
h_inner_base = 5.0; 
h_stopper    = 4.5; 
h_inner_core = h_inner_base + h_stopper; // 10.0mm
h_outer      = 6.0;  

spring_width     = 3.2;
spring_thickness = 4.5;   
z_center         = spring_thickness / 2.0; 

allow_tilt_angle = 30.0; 
span_angle       = 180;
M2_INSERT_BORE   = 3.8;  
CL               = 0.4; 

core_outer_d = 34.0; 
d_outer1     = 50.0; 
d_outer2     = 62.0; 

// ==========================================
// センサ・磁石用パラメータ
// ==========================================
sensor_w            = 17.8; 
sensor_l            = 25.4; 
sensor_pocket_depth = 5.0;  
sensor_hole_pitch_x = 12.0; 
sensor_hole_pitch_y = 20.0; 

magnet_d = 5.2; 
magnet_h = 2.5; 

inner_screw_angles = [0, 90, 180, 270];
inner_screw_radius = 13.5;
inner_insert_depth = 4.5; 

hand_screw_angles = [0, 90, 180, 270];
hand_screw_radius = 22.0; 
hand_boss_d       = 7.0;  
hand_insert_depth = 5.0; 

outer_screw_angles = [45, 135, 225, 315];
outer_screw_radius = (d_outer1 + d_outer2) / 4; 

spring_angles = [22.5, 112.5, 202.5, 292.5];

// ==========================================
// メイン実行部
// ==========================================
if (make_test_cut) {
    intersection() {
        main_model();
        translate([-100, 0, -10]) {
            cube([200, 200, 50]); 
        }
    }
} else {
    main_model();
}

module main_model() {
    union() {
        if (make_base_ring) {
            base_ring();
        }
        if (make_hand_base_plate) {
            translate([0, 0, explode_hand]) {
                hand_base_plate();
            }
        }
        if (make_stopper_ring) {
            stopper_ring();
        }
    }
}

// ==========================================
// ハンド側ベースプレート
// ==========================================
module hand_base_plate() {
    hand_stopper_gap = 1.5; 
    h_rise = (h_inner_base + hand_stopper_gap) - h_outer; 
    thickness = 12.0; 
    
    dome_center_z = z_center + (h_inner_core + CL - z_center) / cos(allow_tilt_angle);
    safe_x = magnet_d / 2 + 0.5; 
    magnet_bottom_z = z_center + (h_inner_core + CL - z_center + safe_x * sin(allow_tilt_angle)) / cos(allow_tilt_angle);
    magnet_roof_z = magnet_bottom_z + magnet_h;
    
    color("orange", 0.8) 
    translate([0, 0, h_outer - 2]) {
        difference() {
            // --- 1. ベース形状 ---
            union() {
                    ring(d_inner=d_outer1, d_outer=d_outer2, h=11, center=false, fn=fn);
                translate([0, 0, 8]) {
                    ring(d_outer=d_outer1, d_inner=core_outer_d + 2*CL, h=h_rise, center=false, fn=fn);
                    translate([0, 0, h_rise]) {
                        cylinder(d=d_outer1, h=thickness, $fn=fn);
                    }
                }
            }
            
            // --- 2. アウター用ネジ穴のくり抜き ---
            for (theta = outer_screw_angles) {
                rotate([0, 0, theta]) {
                    translate([outer_screw_radius, 0, - eps/2]) {
                        cylinder(d=M2_INSERT_BORE, h=11 + h_rise + eps, $fn=30);
                    }
                }
            }
            
            // --- 3. ハンド側ネジ穴のくり抜き ---
            for (theta = hand_screw_angles) {
                rotate([0, 0, theta]) {
                    translate([hand_screw_radius - 4, 0, 8+h_rise]) {
                        cylinder(d=2.1, h=thickness + eps, $fn=30);
                        cylinder(d=4.0, h=thickness + eps - 3, $fn=30);
                    }
                }
            }
            
            // --- 4. エンベロープカッターによる内部クリアランス確保 ---
            translate([0, 0, 8-h_outer]) {
                fast_envelope_cutter(cl=CL);
            }
            
            // --- 5. 磁石用ポケット ---
            translate([0, 0, 8+dome_center_z - h_outer - 1.0]) {
                cylinder(d=magnet_d + 0.4, h=(magnet_roof_z - dome_center_z) + 1.0 + eps, $fn=30);
            }
        }
    }
}

// ==========================================
// 包絡面（エンベロープ）カッター
// ==========================================
module fast_envelope_cutter(cl) {
    cylinder(d=core_outer_d + 2*cl, h=z_center, $fn=fn);
    
    rotate_extrude($fn=fn) {
        intersection() {
            translate([0, -50]) {
                square([100, 150]);
            }
            
            union() {
                // 1. 内輪（コア）の干渉回避ドーム
                for (tilt = [-allow_tilt_angle : 2 : allow_tilt_angle - 2]) {
                    hull() {
                        // Point A
                        translate([0, z_center]) {
                            rotate(-tilt) {
                                translate([-(core_outer_d/2 + cl), -z_center]) {
                                    square([core_outer_d + 2*cl, h_inner_core + cl]);
                                }
                            }
                        }
                        // Point B
                        translate([0, z_center]) {
                            rotate(-(tilt + 2)) {
                                translate([-(core_outer_d/2 + cl), -z_center]) {
                                    square([core_outer_d + 2*cl, h_inner_core + cl]);
                                }
                            }
                        }
                    }
                }
                
                // 2. ★追加: ばねの跳ね上がりを吸収する「すり鉢状のテーパー逃げ」
                // ばね空間（半径16〜24mm）の真上を、内側に向かって高く（最大13.5mm）斜めにくり抜く
                polygon([
                    [core_outer_d/2 - 1.0, 0],
                    [d_outer1/2 - 1.0,     0],
                    [d_outer1/2 - 1.0,     5.5],
                    [core_outer_d/2 - 1.0, 13.5]
                ]);
            }
        }
    }
}

// ==========================================
// ベースリング（内輪・外輪・スパイラルばね）
// ==========================================
module base_ring() {
    
    // --- 内輪 ---
    gray04() 
    difference() {
        cylinder(d=core_outer_d, h=h_inner_core, $fn=fn);
        
        // 内側ネジ穴
        for (theta = [0, 180]) {
            rotate([0, 0, theta]) {
                translate([inner_screw_radius, 0, -eps]) {
                    #cylinder(d=M2_INSERT_BORE, h=inner_insert_depth + eps, $fn=30);
                }
            }
        }
        
        // センサー用ポケット
        translate([-(sensor_w + 0.5)/2, -(sensor_l + 0.5)/2, h_inner_core - sensor_pocket_depth + eps]) {
            cube([sensor_w + 0.5, sensor_l + 0.5, sensor_pocket_depth]);
        }
            
        // コネクタ逃げ穴（7.5 x 2.5mm）
        translate([-3.75, 12.7, h_inner_core - sensor_pocket_depth + eps]) {
            cube([7.5, 3.5, sensor_pocket_depth]);
        }
            
        // ルーティング溝
        hull() {
            translate([3.5, 14.0, h_inner_core - sensor_pocket_depth + eps]) {
                cylinder(d=3.5, h=sensor_pocket_depth, $fn=30);
            }
            translate([9.5, 9.5, h_inner_core - sensor_pocket_depth + eps]) {
                cylinder(d=4.0, h=sensor_pocket_depth, $fn=30);
            }
        }
        
        // ケーブル用ドロップ穴 (4.3 x 8.5mm)
        translate([9.0 - 1.0, 9.0 - 7.5, -eps]) {
            cube([4.3, 8.5, h_inner_core + 2*eps]);
        }
        
        // センサー穴
        for(dx = [-1, 1], dy = [-1, 1]) {
            translate([dx * sensor_hole_pitch_x/2, dy * sensor_hole_pitch_y/2, -eps]) {
                cylinder(d=1.8, h=h_inner_core - sensor_pocket_depth + 2*eps, $fn=30);
            }
        }
    }  

    // --- 外輪 ---
    gray08()
    translate([0, 0, 0.2*eps]) {
        difference() { 
            ring(d_inner=d_outer1, d_outer=d_outer2, h=4.5, center=false, fn=fn);
            
            for (theta = outer_screw_angles) {
                rotate([0, 0, theta]) {
                    translate([outer_screw_radius, 0, -eps/2]) {
                        cylinder(d=2.1, h=h_outer + eps, $fn=30);
                    }
                }
            }
        }
    }

    r_in_wall  = core_outer_d / 2; 
    r_out_wall = d_outer1 / 2; 
    iz         = spring_thickness;
    
    // --- ばね固定ブロック ---
    gray08() {
        for (theta = spring_angles) { 
            rotate([0, 0, theta + span_angle]) {
                translate([r_in_wall - 1.0, 0, iz/2]) {
                    cube(size=[4.0, 4.0, iz], center = true);
                }
            }
        }
        for (theta = spring_angles) { 
            rotate([0, 0, theta]) {
                translate([r_out_wall + 1.0, 0, iz/2]) {
                    cube(size=[4.0, 4.0, iz], center = true);
                }
            }
        }
    }
    
    // --- スパイラルばね ---
    color("salmon") {
        for (theta = spring_angles) { 
            rotate([0, 0, theta]) {
                translate([0, 0, 0.3*eps]) {
                    spiral_spring_arm(
                        r_start    = r_out_wall + 0.5, 
                        r_end      = r_in_wall - 0.5,  
                        span_angle = span_angle,              
                        thickness  = spring_width,
                        h          = spring_thickness
                    );
                }
            }
        }
    }
}

// ==========================================
// ストッパーリング
// ==========================================
module stopper_ring() {
    color("blue", 0.8) // 全体の色をオレンジに統一
    difference() {
        // くり抜かれる側の元の形状（unionで一体化）
        union() {
            translate([0, 0, -3.5]) {
                ring(d_inner=d_outer1, d_outer=d_outer2, h=3.5, center=false, fn=fn);
            }
            translate([0, 0, -7]) {
                ring(d_inner=core_outer_d+2, d_outer=d_outer2, h=7-3.5, center=false, fn=fn);
            }
        }
        
        // ★ z=2 を基準に Z軸反転させたエンベロープカッター
        translate([0, 0, 2]) {
            mirror([0, 0, 1]) {
                translate([0, 0, -2]) {
                    fast_envelope_cutter(cl=CL);
                }
            }
        }
        
        for (theta = outer_screw_angles) {
            rotate([0, 0, theta]) {
                translate([outer_screw_radius, 0, -7 - eps/2]) {
                    cylinder(d=2.1, h=7 + eps, $fn=30);
                    cylinder(d=4.2, h=5 + eps, $fn=30);
                }
            }
        }
    }
}

// ==========================================
// 共通幾何学サブモジュール
// ==========================================
module spiral_spring_arm(r_start, r_end, span_angle, thickness, h) {
    steps = 60;
    points = concat(
        [for (i = [0:steps]) 
            [
                (r_start - (r_start - r_end) * i / steps + thickness/2) * cos(span_angle * i / steps), 
                (r_start - (r_start - r_end) * i / steps + thickness/2) * sin(span_angle * i / steps)
            ]
        ],
        [for (i = [steps:-1:0]) 
            [
                (r_start - (r_start - r_end) * i / steps - thickness/2) * cos(span_angle * i / steps), 
                (r_start - (r_start - r_end) * i / steps - thickness/2) * sin(span_angle * i / steps)
            ]
        ]
    );
    linear_extrude(height=h) { 
        polygon(points); 
    }
}

module ring(d_outer, d_inner, h, fn=fn, center=false) {
    difference() {
        cylinder(d=d_outer, h=h, $fn=fn, center=center);
        translate([0, 0, -eps]) {
            cylinder(d=d_inner, h=h + 2*eps, $fn=fn, center=center);
        }
    }
}

module gray04() { 
    if (use_colors) color([0.3, 0.3, 0.3]) children(); else children(); 
}
module gray08() { 
    if (use_colors) color([0.8, 0.8, 0.8]) children(); else children(); 
}