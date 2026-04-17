`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 02/21/2026 12:47:56 PM
// Design Name: 
// Module Name: VGA_640x480_Timing
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

module VGA_640x480_Timing(
    input  logic        i_Clock,    
    input  logic        i_Reset,
    output logic        o_HSync,
    output logic        o_VSync,
    output logic [9:0]  o_X,        // current pixel column (0-639 valid)
    output logic [9:0]  o_Y,        // current pixel row    (0-479 valid)
    output logic        o_Active    // high when in visible area
);

    // 640x480 @ ~60 Hz using 25 MHz pixel clock
    // Horizontal: 640 visible + 16 FP + 96 sync + 48 BP = 800 total
    // Vertical:   480 visible + 10 FP +  2 sync + 33 BP = 525 total

    localparam int H_VISIBLE = 640;
    localparam int H_FP      = 16;
    localparam int H_SYNC    = 96;
    localparam int H_BP      = 48;
    localparam int H_TOTAL   = H_VISIBLE + H_FP + H_SYNC + H_BP;

    localparam int V_VISIBLE = 480;
    localparam int V_FP      = 10;
    localparam int V_SYNC    = 2;
    localparam int V_BP      = 33;
    localparam int V_TOTAL   = V_VISIBLE + V_FP + V_SYNC + V_BP;

    logic [9:0] h_cnt;
    logic [9:0] v_cnt;

    always_ff @(posedge i_Clock) begin
        if (i_Reset) begin
            h_cnt <= 10'd0;
            v_cnt <= 10'd0;
        end else begin
            if (h_cnt == H_TOTAL - 1) begin
                h_cnt <= 10'd0;
                if (v_cnt == V_TOTAL - 1)
                    v_cnt <= 10'd0;
                else
                    v_cnt <= v_cnt + 10'd1;
            end else begin
                h_cnt <= h_cnt + 10'd1;
            end
        end
    end

    assign o_HSync  = ~((h_cnt >= H_VISIBLE + H_FP) &&
                        (h_cnt <  H_VISIBLE + H_FP + H_SYNC));

    assign o_VSync  = ~((v_cnt >= V_VISIBLE + V_FP) &&
                        (v_cnt <  V_VISIBLE + V_FP + V_SYNC));

    assign o_Active = (h_cnt < H_VISIBLE) && (v_cnt < V_VISIBLE);
    assign o_X      = h_cnt;
    assign o_Y      = v_cnt;

endmodule