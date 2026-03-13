`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 01/28/2026 12:38:58 PM
// Design Name: 
// Module Name: SevenSeg_2Digit_Mux
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

(* keep_hierarchy = "yes" *)
module SevenSeg_2Digit_Mux (
    input  logic        i_Clock,
    input  logic        i_Reset,
    input  logic [7:0]  i_Byte,        //value to show as hex (2 digits)

    output logic [6:0]  seg,           
    output logic [7:0]  an,            
    output logic        dp             //decimal point
);

    //multiplex toggle (~1kHz)
    logic [16:0] refresh_cnt;
    logic        digit_sel; //0=low nibble, 1=high nibble

    always_ff @(posedge i_Clock) begin
        if (i_Reset) begin
            refresh_cnt <= 17'd0;
            digit_sel   <= 1'b0;
        end else begin
            refresh_cnt <= refresh_cnt + 17'd1;
            if (refresh_cnt == 17'd100000) begin
                refresh_cnt <= 17'd0;
                digit_sel   <= ~digit_sel;
            end
        end
    end

    logic [3:0] nibble;
    assign nibble = digit_sel ? i_Byte[7:4] : i_Byte[3:0];

    logic segA, segB, segC, segD, segE, segF, segG;

    Binary_To_7Segment u_digit (
        .i_Clk        (i_Clock),
        .i_Binary_Num (nibble),
        .o_Segment_A  (segA),
        .o_Segment_B  (segB),
        .o_Segment_C  (segC),
        .o_Segment_D  (segD),
        .o_Segment_E  (segE),
        .o_Segment_F  (segF),
        .o_Segment_G  (segG)
    );

    assign seg[0] = ~segA; 
    assign seg[1] = ~segB; 
    assign seg[2] = ~segC; 
    assign seg[3] = ~segD; 
    assign seg[4] = ~segE; 
    assign seg[5] = ~segF; 
    assign seg[6] = ~segG; 

    //dp off (active-low)
    assign dp = 1'b1;
    assign an = digit_sel ? 8'b1111_1101 : 8'b1111_1110;

endmodule
