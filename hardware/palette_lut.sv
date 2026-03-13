module palette_lut (
    input  logic         clk,
    input  logic [15:0]  iter_in,
    input  logic [15:0]  max_iter,
    input  logic [7:0]   palette_id,
    output logic [7:0]   rgb_r,
    output logic [7:0]   rgb_g,
    output logic [7:0]   rgb_b
);
    // simple normalized value
    logic [15:0] v;
    always_comb begin
        if (iter_in >= max_iter) v = 16'hFFFF;
        else v = (iter_in * 16'hFFFF) / max_iter;
    end

    // palette cases: palette_id selects color scheme
    always_comb begin
        case (palette_id)
            8'd0: begin // grayscale
                rgb_r = v[15:8];
                rgb_g = v[15:8];
                rgb_b = v[15:8];
            end
            8'd1: begin // blue->cyan->white
                rgb_r = (v[15:8] >> 1);
                rgb_g = v[15:8];
                rgb_b = 8'hFF;
            end
            8'd2: begin // psychedelic
                rgb_r = v[15:8] ^ (v[7:0]);
                rgb_g = ~v[15:8];
                rgb_b = v[7:0];
            end
            default: begin
                rgb_r = v[15:8];
                rgb_g = v[15:8];
                rgb_b = v[15:8];
            end
        endcase
    end
endmodule