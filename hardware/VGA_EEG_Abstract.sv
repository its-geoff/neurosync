`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 02/21/2026 02:15:30 PM
// Design Name: 
// Module Name: VGA_EEG_Abstract
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

module VGA_EEG_Abstract (
    input  logic        i_Clock,
    input  logic        i_Reset,
    input  logic        i_Active,
    input  logic [9:0]  i_X,
    input  logic [9:0]  i_Y,
    input  logic        i_VSync,    

    input  logic [15:0] i_Delta,
    input  logic [15:0] i_Theta,
    input  logic [15:0] i_Alpha,
    input  logic [15:0] i_Beta,

    output logic [3:0]  o_Red,
    output logic [3:0]  o_Green,
    output logic [3:0]  o_Blue
);

    //Triangle wave: byte -> smooth 4-bit ramp (0->15->0->15...)
    function automatic [3:0] tri4;
        input [7:0] v;
        tri4 = v[7] ? ~v[6:3] : v[6:3];
    endfunction

    //Saturating 4-bit add (result capped at 0xF)
    function automatic [3:0] sadd;
        input [3:0] a, b;
        logic [4:0] s;
        s    = {1'b0, a} + {1'b0, b};
        sadd = s[4] ? 4'hF : s[3:0];
    endfunction

    //(val * amp) >> 4  -- scales pattern brightness by band amplitude
    function automatic [3:0] scale4;
        input [3:0] val, amp;
        logic [7:0] prod;
        prod   = {4'd0, val} * {4'd0, amp};
        scale4 = prod[7:4];
    endfunction

    //VSync falling-edge detector -> one frame_tick pulse per frame (~60 Hz)
    logic vsync_prev, frame_tick;
    always_ff @(posedge i_Clock) begin
        vsync_prev <= i_VSync;
        frame_tick <= vsync_prev && !i_VSync;
    end

    //Phase counters: two per band, incrementing at slightly different speeds
    //Speed = 1 + band[15:12]  (range 1-17 steps/frame)
    //The tiny +1 offset between the pair creates an organic beat frequency
    logic [7:0] ph_d0, ph_d1;
    logic [7:0] ph_t0, ph_t1;
    logic [7:0] ph_a0, ph_a1;
    logic [7:0] ph_b0, ph_b1;

    always_ff @(posedge i_Clock) begin
        if (i_Reset) begin
            ph_d0 <= 8'd0;   ph_d1 <= 8'd128;
            ph_t0 <= 8'd48;  ph_t1 <= 8'd160;
            ph_a0 <= 8'd96;  ph_a1 <= 8'd208;
            ph_b0 <= 8'd144; ph_b1 <= 8'd32;
        end else if (frame_tick) begin
            ph_d0 <= ph_d0 + 8'd1 + {4'd0, i_Delta[15:12]};
            ph_d1 <= ph_d1 + 8'd2 + {4'd0, i_Delta[15:12]};

            ph_t0 <= ph_t0 + 8'd1 + {4'd0, i_Theta[15:12]};
            ph_t1 <= ph_t1 + 8'd2 + {4'd0, i_Theta[15:12]};

            ph_a0 <= ph_a0 + 8'd1 + {4'd0, i_Alpha[15:12]};
            ph_a1 <= ph_a1 + 8'd2 + {4'd0, i_Alpha[15:12]};

            ph_b0 <= ph_b0 + 8'd2 + {4'd0, i_Beta[15:12]};
            ph_b1 <= ph_b1 + 8'd3 + {4'd0, i_Beta[15:12]};
        end
    end

    //Pixel coordinates
    wire [8:0] diag_sum  = {1'b0, i_X[7:0]} + {1'b0, i_Y[7:0]};  //NW-SE  0..510
    wire [8:0] diag_diff = {1'b0, i_X[7:0]} - {1'b0, i_Y[7:0]};  //NE-SW  wraps

    //Manhattan distance from centre for radial delta pattern
    wire [9:0] mdx    = (i_X >= 10'd320) ? (i_X - 10'd320) : (10'd320 - i_X);
    wire [9:0] mdy    = (i_Y >= 10'd240) ? (i_Y - 10'd240) : (10'd240 - i_Y);
    wire [8:0] radial = mdx[8:1] + mdy[8:1];

    //delta: two radial ring waves
    wire [4:0] d_sum = {1'b0, tri4(radial[7:0] + ph_d0)}
                     + {1'b0, tri4(radial[7:0] + ph_d1)};
    wire [3:0] d_pat = d_sum[4:1];

    //theta: NW-SE wave + NE-SW wave crossing at 90 degrees
    wire [4:0] t_sum = {1'b0, tri4(diag_sum[7:0]  + ph_t0)}
                     + {1'b0, tri4(diag_diff[7:0] + ph_t1)};
    wire [3:0] t_pat = t_sum[4:1];

    //alpha: two close diagonal waves making wide smooth flowing bands
    wire [4:0] a_sum = {1'b0, tri4(diag_sum[7:0] + ph_a0)}
                     + {1'b0, tri4(diag_sum[7:0] + ph_a1)};
    wire [3:0] a_pat = a_sum[4:1];

    //beta: fast ripple mixing both diagonal axes slightly
    wire [7:0] b_mix_coord = diag_sum[7:0] + {3'b0, diag_diff[7:3]};
    wire [4:0] b_sum = {1'b0, tri4(diag_sum[7:0] + ph_b0)}
                     + {1'b0, tri4(b_mix_coord    + ph_b1)};
    wire [3:0] b_pat = b_sum[4:1];

    //scale each pattern by band amplitude (top nibble of 16-bit value)
    wire [3:0] amp_d = i_Delta[15:12];
    wire [3:0] amp_t = i_Theta[15:12];
    wire [3:0] amp_a = i_Alpha[15:12];
    wire [3:0] amp_b = i_Beta[15:12];

    wire [3:0] d_s = scale4(d_pat, amp_d);
    wire [3:0] t_s = scale4(t_pat, amp_t);
    wire [3:0] a_s = scale4(a_pat, amp_a);
    wire [3:0] b_s = scale4(b_pat, amp_b);

    wire [3:0] r_pat = sadd(sadd(a_s, {1'b0, d_s[3:1]}), {1'b0, b_s[3:1]});
    wire [3:0] g_pat = sadd(sadd(t_s, {1'b0, a_s[3:1]}), {2'b0, d_s[3:2]});
    wire [3:0] b_pat2 = sadd(sadd(d_s, b_s),             {1'b0, t_s[3:1]});

    wire [3:0] r_out = sadd(r_pat, {1'b0, amp_a[3:1]});
    wire [3:0] g_out = sadd(g_pat, {1'b0, amp_t[3:1]});
    wire [3:0] b_out = sadd(b_pat2, {1'b0, amp_d[3:1]});

    always_ff @(posedge i_Clock) begin
        if (!i_Active) begin
            o_Red   <= 4'h0;
            o_Green <= 4'h0;
            o_Blue  <= 4'h0;
        end else begin
            o_Red   <= r_out;
            o_Green <= g_out;
            o_Blue  <= b_out;
        end
    end

endmodule